import { HttpError, ApiService } from "@/services/api";

export const handleOAuthRequestsIn = async <T>(fn: () => Promise<T>, api: ApiService): Promise<T> => {
  while (true) {
    try {
      return await fn()
    } catch (e) {
      const authRequest = parseAuthRequest(e);
      if (authRequest) {
        if (authRequest instanceof OAuthRequest) {
          await oauthPopupFlow(authRequest, api);
        } else if (authRequest instanceof AuthTokenRequest) {
          await authTokenPopupFlow(authRequest, api);
        }
        continue;
      }
      throw e;
    }
  }
}

const parseAuthRequest = (e: unknown): OAuthRequest | AuthTokenRequest | undefined => {
  if (!(e instanceof HttpError && e.status === 401 && e.body)) {
    return undefined
  }
  try {
    const body = JSON.parse(e.body);
    if (!body.detail) {
      return undefined
    }
    if (body.detail.requestType === "oauth") {
      return new OAuthRequest(body.detail.oauthUrl, body.detail.oauthState, body.detail.agentId);
    }
    if (body.detail.requestType === "auth_token") {
      return new AuthTokenRequest(body.detail.toolId, body.detail.agentId);
    }
    return undefined
  } catch (_) {
    return undefined
  }
}

class OAuthRequest {
  url: string
  state: string
  agentId: number

  constructor(url: string, state: string, agentId: number) {
    this.url = url;
    this.state = state;
    this.agentId = agentId;
  }
}

class AuthTokenRequest {
  toolId: string
  agentId: number

  constructor(toolId: string, agentId: number) {
    this.toolId = toolId;
    this.agentId = agentId;
  }
}

export class AuthenticationError extends Error {
  errorCode: string

  constructor(errorCode: string) {
    super('Authentication error: ' + errorCode);
    this.errorCode = errorCode;
  }
}

const oauthPopupFlow = async (oauthRequest: OAuthRequest, api: ApiService): Promise<void> => {
  return new Promise((resolve, reject) => {
    const popupWidth = 600;
    const popupHeight = 600;
    const left = window.screenX + (window.outerWidth - popupWidth) / 2;
    const top = window.screenY + (window.outerHeight - popupHeight) / 2;
    const popup = window.open(oauthRequest.url, 'oauth', `popup,width=${popupWidth},height=${popupHeight},left=${left},top=${top}`);
    if (!popup) {
      reject(new AuthenticationError('authenticationWindowBlocked'));
      return;
    }

    // using broadcast channel instead of just using popup and window opener since some mcp servers (like sentry)
    // can set Cross Origin Opener Policy (COOP) which prevents the popup from accessing the opener window
    const channel = new BroadcastChannel('oauth_channel');
    const cleanup = () => {
      channel.close();
      channel.removeEventListener('message', handleCallback);
    };

    const handleCallback = async (event: MessageEvent) => {
      const data = event.data;
      if (data.type === 'oauth_callback' && data.state === oauthRequest.state) {
        try {
          cleanup();
          if (data.error) {
            await api.deleteToolAuth(data.toolId, data.state);
            reject(new AuthenticationError(data.error == 'access_denied' ? 'authenticationAccessDenied' : 'authenticationUnknownError'));
          } else {
            await api.completeToolOauthAuth(data.toolId, oauthRequest.agentId, data.state, data.code);
            resolve()
          }
        } catch (error) {
          if (error instanceof HttpError && error.status === 400) {
            try {
              const body = JSON.parse(error.body);
              if (body.detail && body.detail === "Authentication cancelled") {
                reject(new AuthenticationError('authenticationCancelled'));
                return
              }
            } catch (_) {
            }
          }
          reject(error);
        }
      }
    };

    channel.addEventListener('message', handleCallback);
  });
}

const authTokenPopupFlow = async (request: AuthTokenRequest, api: ApiService): Promise<void> => {
  return new Promise((resolve, reject) => {
    const popupWidth = 850;
    const popupHeight = 400;
    const left = window.screenX + (window.outerWidth - popupWidth) / 2;
    const top = window.screenY + (window.outerHeight - popupHeight) / 2;
    const url = `${window.location.origin}/tools/${request.toolId}/agents/${request.agentId}/auth-token`;
    const popup = window.open(url, 'authToken', `popup,width=${popupWidth},height=${popupHeight},left=${left},top=${top}`);
    if (!popup) {
      reject(new AuthenticationError('authenticationWindowBlocked'));
      return;
    }

    const channel = new BroadcastChannel('auth_token_channel');
    const cleanup = () => {
      channel.close();
      channel.removeEventListener('message', handleCallback);
    };

    const handleCallback = async (event: MessageEvent) => {
      const data = event.data;
      if (data.type === 'auth_token_result' && data.toolId === request.toolId && data.agentId === request.agentId) {
        cleanup();
        if (data.success) {
          resolve();
        } else {
          reject(new AuthenticationError(data.cancelled ? 'authenticationCancelled' : 'authenticationAccessDenied'));
        }
      }
    };

    channel.addEventListener('message', handleCallback);
  });
}
