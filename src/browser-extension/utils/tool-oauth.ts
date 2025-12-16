import { browser } from "wxt/browser";
import { HttpServiceError } from "./http";
import { fetchJson } from "./http";
import { Agent } from "./agent";
import { AuthService } from "./auth";

export const handleOAuthRequestsIn = async <T>(
  fn: () => Promise<T>,
  agent: Agent,
  authService?: AuthService
): Promise<T> => {
  while (true) {
    try {
      return await fn();
    } catch (e) {
      const oauthRequest = parseOAuthRequest(e);
      if (oauthRequest) {
        await oauthExtensionFlow(oauthRequest, agent, authService);
      } else {
        throw e;
      }
    }
  }
};

const parseOAuthRequest = (e: unknown): { url: string; state: string } | undefined => {
  if (!(e instanceof HttpServiceError && e.status === 401 && e.body)) {
    return undefined;
  }
  try {
    const body = JSON.parse(e.body);
    if (!body.detail) {
      return undefined;
    }
    return new OAuthRequest(body.detail?.oauthUrl, body.detail?.oauthState);
  } catch (_) {
    return undefined;
  }
};

class OAuthRequest {
  url: string;
  state: string;

  constructor(url: string, state: string) {
    this.url = url;
    this.state = state;
  }
}

export class AuthenticationError extends Error {
  errorCode: string;

  constructor(errorCode: string) {
    super("Authentication error: " + errorCode);
    this.errorCode = errorCode;
  }
}

const oauthExtensionFlow = async (
  oauthRequest: OAuthRequest,
  agent: Agent,
  authService?: AuthService
): Promise<void> => {
  try {
    const redirectUrl = await browser.identity.launchWebAuthFlow({
      interactive: true,
      url: oauthRequest.url,
    });

    if (!redirectUrl) {
      throw new AuthenticationError("authenticationCancelled");
    }

    const url = new URL(redirectUrl);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const error = url.searchParams.get("error");
    const toolId = url.searchParams.get("toolId");

    if (state !== oauthRequest.state) {
      throw new AuthenticationError("authenticationStateMismatch");
    }

    if (error) {
      if (toolId) {
        await deleteToolAuth(agent, toolId, state!, authService);
      }
      throw new AuthenticationError(error == "access_denied" ? "authenticationAccessDenied" : "authenticationUnknownError");
    }

    if (!code || !toolId) {
      throw new AuthenticationError("authenticationCancelled");
    }

    await completeToolAuth(agent, toolId, state!, code, authService);
  } catch (error: any) {
    if (error?.message?.includes("The user canceled the sign-in flow")) {
      throw new AuthenticationError("authenticationCancelled");
    }
    if (error instanceof HttpServiceError && error.status === 400) {
      try {
        const body = JSON.parse(error.body || "{}");
        if (body.detail && body.detail === "Authentication cancelled") {
          throw new AuthenticationError("authenticationCancelled");
        }
      } catch (_) {}
    }
    throw error;
  }
};

const completeToolAuth = async (
  agent: Agent,
  toolId: string,
  state: string,
  code: string,
  authService?: AuthService
): Promise<void> => {
  await fetchJson(
    `${agent.url}/api/tools/${toolId}/oauth/${state}`,
    await Agent.buildHttpRequest("PUT", { code }, authService)
  );
};

const deleteToolAuth = async (
  agent: Agent,
  toolId: string,
  state: string,
  authService?: AuthService
): Promise<void> => {
  await fetchJson(
    `${agent.url}/api/tools/${toolId}/oauth/${state}`,
    await Agent.buildHttpRequest("DELETE", undefined, authService)
  );
};
