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

const parseOAuthRequest = (e: unknown): { url: string; state: string; agentId: number } | undefined => {
  if (!(e instanceof HttpServiceError && e.status === 401 && e.body)) {
    return undefined;
  }
  try {
    const body = JSON.parse(e.body);
    if (!body.detail) {
      return undefined;
    }
    return new OAuthRequest(body.detail?.oauthUrl, body.detail?.oauthState, body.detail?.agentId);
  } catch (_) {
    return undefined;
  }
};

class OAuthRequest {
  url: string;
  state: string;
  agentId: number;

  constructor(url: string, state: string, agentId: number) {
    this.url = url;
    this.state = state;
    this.agentId = agentId;
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
    const redirectUrl = await new Promise<string>((resolve, reject) => {
      browser.windows.create({
        url: oauthRequest.url,
        type: 'popup',
        width: 600,
        height: 600,
      }).then((window) => {
        if (!window?.tabs?.[0]) {
          reject(new Error('Failed to create popup'));
          return;
        }

        const windowId = window.id!;
        const tabId = window.tabs[0].id!;
        let resolved = false;

        const cleanup = () => {
          if (resolved) return;
          resolved = true;
          browser.tabs.onUpdated.removeListener(tabUpdateListener);
          browser.windows.onRemoved.removeListener(windowRemovedListener);
          browser.windows.remove(windowId).catch(() => {});
        };

        const isCallbackUrl = (url: string): boolean => {
          try {
            const parsedUrl = new URL(url);
            return parsedUrl.pathname.match(/\/tools\/[^\/]+\/oauth-callback/) !== null && 
                   (parsedUrl.searchParams.has('code') || parsedUrl.searchParams.has('error'));
          } catch (_) {
            return false;
          }
        };

        const tabUpdateListener = (updatedTabId: number, changeInfo: { url?: string }) => {
          if (resolved || updatedTabId !== tabId) return;
          if (changeInfo.url && isCallbackUrl(changeInfo.url)) {
            cleanup();
            resolve(changeInfo.url);
          }
        };

        const windowRemovedListener = (removedWindowId: number) => {
          if (removedWindowId === windowId && !resolved) {
            cleanup();
            reject(new AuthenticationError("authenticationCancelled"));
          }
        };

        browser.tabs.onUpdated.addListener(tabUpdateListener);
        browser.windows.onRemoved.addListener(windowRemovedListener);
      }).catch(reject);
    });

    const url = new URL(redirectUrl);
    const code = url.searchParams.get("code");
    const state = url.searchParams.get("state");
    const error = url.searchParams.get("error");
    const toolId = url.pathname.match(/\/tools\/([^\/]+)\/oauth-callback/)?.[1];

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

    await completeToolAuth(agent, toolId, oauthRequest.agentId, state!, code, authService);
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
  agentId: number,
  state: string,
  code: string,
  authService?: AuthService
): Promise<void> => {
  await fetchJson(
    `${agent.url}/api/tools/${toolId}/agents/${agentId}/auth`,
    await Agent.buildHttpRequest("PUT", { state, code }, authService)
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
