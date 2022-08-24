import { DialogService } from "aurelia-dialog";
import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject } from "aurelia-framework";
import { LoginDialog } from "resources/elements/login-dialog";
import { AUTH_EVENTS_CHANNEL, REQUEST_FRESH_LOGIN_CHANNEL, REQUEST_LOGOUT_CHANNEL } from "resources/events";
import { ApiLink, ApiObject, isApiObject } from "./api-objects";
import { BaseApiService } from "./base-api";

interface ApiTokenApiObject extends ApiObject {
    accessToken: string;
    refreshToken?: string;
}

// Event content constants
export const LOGIN_EXPIRES_SOON = "Login expires soon";
export const LOGIN_EXPIRED = "Login is expired";
export const LOGIN = "User is logged in";
export const LOGIN_RENEWED = "User logged in with password again";
export const LOGIN_TOKEN_REFRESHED = "New login token aquired";
export const LOGOUT = "User is logged out";

export function isApiTokenApiObject(obj: ApiObject): obj is ApiTokenApiObject {
    return (obj as any).accessToken != null;
}

@autoinject
export class AuthenticationService {

    private ACCESS_TOKEN_KEY: string = "MUSE4Anything_JWT";
    private REFRESH_TOKEN_KEY: string = "MUSE4Anything_JWT_REFRESH";
    private currentApiToken: string;
    private keepLogin: boolean = false;

    private isLoggedInStatus: boolean = false;
    private userStatus: any = null;

    private api: BaseApiService;
    private events: EventAggregator;
    private dialogService: DialogService;

    constructor(baseApi: BaseApiService, eventAggregator: EventAggregator, dialogService: DialogService) {
        this.api = baseApi;
        this.events = eventAggregator;
        this.dialogService = dialogService;
        this.recoverLogin();
        this.checkTokenExpiration();
        window.setInterval(() => this.checkTokenExpiration(), 60000);
        this.events.subscribe(REQUEST_FRESH_LOGIN_CHANNEL, (callbacks) => this.ensureFreshLogin(callbacks.resolve, callbacks.reject));
        this.events.subscribe(REQUEST_LOGOUT_CHANNEL, () => this.logout());
    }

    public get currentStatus(): { isLoggedIn: boolean, user: any } {
        return {
            isLoggedIn: this.isLoggedInStatus,
            user: this.userStatus,
        };
    }

    private apiTokenChanged(newToken: string, oldToken: string) {
        // TODO
        const wasLoggedIn = this.isLoggedInStatus;
        this.isLoggedInStatus = this.isLoggedIn();
        if (newToken != null) {
            this.api.defaultAuthorization = `Bearer ${newToken}`;
        } else {
            this.api.resetDefaultAuthorization();
        }
        if (!wasLoggedIn && this.isLoggedInStatus) {
            this.events.publish(AUTH_EVENTS_CHANNEL, LOGIN);
        } else {
            this.events.publish(AUTH_EVENTS_CHANNEL, LOGIN_TOKEN_REFRESHED);
            // TODO send distinct message for fresh login tokens
        }
    }

    private checkTokenExpiration() {
        console.log("Check token expiration")
        const refreshToken = this.getRefreshToken();
        if (refreshToken == null) {
            return;
        }
        const token = this.currentApiToken;
        if (token == null || this.expiresSoon(token)) {
            this.refreshToken();
        }
    }

    public login(username_or_email: string, password: string, keepLogin: boolean = false): void {
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
        this.api.searchResolveRels("login")
            .then((loginLink: ApiLink) => {
                return this.api.submitByApiLink(loginLink, {
                    username: username_or_email,
                    password: password,
                });
            })
            .then(response => {
                if (!isApiObject(response.data) || !isApiTokenApiObject(response.data)) {
                    return; // TODO show error
                }
                this.keepLogin = keepLogin;

                this.updateCredentials(response.data.accessToken, response.data.refreshToken, keepLogin);
            });
    }

    public freshLogin(password: string): Promise<string> {
        return this.api.searchResolveRels("fresh-login")
            .then((loginLink: ApiLink) => {
                return this.api.submitByApiLink(loginLink, {
                    password: password,
                });
            })
            .then(response => {
                if (!isApiObject(response.data) || !isApiTokenApiObject(response.data)) {
                    // TODO show error
                    throw new Error("Login failed!");
                }

                this.updateCredentials(response.data.accessToken, response.data.refreshToken, this.keepLogin);
                return response.data.accessToken;
            });
    }


    public ensureFreshLogin(resolve: (value: string) => void, reject?: (value: unknown) => void): void {
        if (this.tokenIsFresh()) {
            resolve(this.currentApiToken);
            return;
        }
        this.dialogService.open({
            viewModel: LoginDialog,
            model: { isPasswordOnly: true, title: "titles.fresh-login" },
            lock: false,
        }).whenClosed((result) => {
            if (!result.wasCancelled && result.output?.password) {
                this.freshLogin(result.output?.password).then(resolve, reject);
            } else {
                reject("cancelled by user");
            }
        });
    }

    public logout() {
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
        sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
        localStorage.removeItem(this.ACCESS_TOKEN_KEY);
        sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
        this.api.resetDefaultAuthorization();
        this.isLoggedInStatus = false;
        this.api.clearCaches(true);
        this.events.publish(AUTH_EVENTS_CHANNEL, LOGOUT);
    }

    private refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (refreshToken != null && this.expiresSoon(refreshToken, 60)) {
            this.events.publish(AUTH_EVENTS_CHANNEL, LOGIN_EXPIRES_SOON);
        }
        if (refreshToken == null || this.expiration(refreshToken) < new Date()) {
            this.events.publish(AUTH_EVENTS_CHANNEL, LOGIN_EXPIRED);
        }
        this.api.searchResolveRels("refresh")
            .then((refreshLink: ApiLink) => {
                return this.api.submitByApiLink(refreshLink, undefined, undefined, `Bearer ${refreshToken}`);
            })
            .then(response => {
                if (!isApiObject(response.data) || !isApiTokenApiObject(response.data)) {
                    return; // TODO show error
                }

                this.updateCredentials(response.data.accessToken, null, this.keepLogin);
            });
    }

    private recoverLogin() {
        const refreshToken = this.getRefreshToken();

        if (refreshToken == null) {
            return;
        }

        let accessToken = sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
        if (accessToken == null) {
            accessToken = localStorage.getItem(this.ACCESS_TOKEN_KEY);
        }
        const oldApiToken = this.currentApiToken;
        this.currentApiToken = accessToken;
        this.apiTokenChanged(this.currentApiToken, oldApiToken);
        console.log("recovered login")
    }

    private updateCredentials(apiToken: string, apiRefreshToken?: string, keepLogin: boolean = false) {
        const oldToken = this.currentApiToken;
        // TODO check for validity!
        this.currentApiToken = apiToken;
        if (keepLogin) {
            localStorage.setItem(this.ACCESS_TOKEN_KEY, apiToken);
        } else {
            sessionStorage.setItem(this.ACCESS_TOKEN_KEY, apiToken);
        }

        // TODO store apiRefreshToken long term (local storage or (html-)cookie?)
        if (apiRefreshToken != null) {
            if (keepLogin) {
                localStorage.setItem(this.REFRESH_TOKEN_KEY, apiRefreshToken);
            } else {
                sessionStorage.setItem(this.REFRESH_TOKEN_KEY, apiRefreshToken);
            }
        }

        if (this.currentApiToken !== oldToken) {
            this.apiTokenChanged(apiToken, oldToken);
        }
    }

    private getRefreshToken(): string {
        let token = sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
        if (token == null) {
            token = localStorage.getItem(this.REFRESH_TOKEN_KEY);
        }
        return token;
    }

    private tokenToJson(token: string) {
        return JSON.parse(atob(token.split('.')[1]));
    }

    private expiration(token: string): Date {
        const decoded = this.tokenToJson(token);
        const exp = new Date(0);
        exp.setUTCSeconds(decoded.exp);
        return exp;
    }

    private isLoggedIn(): boolean {
        const currentDate = new Date();
        if (this.currentApiToken != null) {
            return this.expiration(this.currentApiToken) > currentDate;
        }
        const token = this.getRefreshToken();
        return (token != null) && (this.expiration(token) > currentDate);
    }

    private expiresSoon(token: string, timedeltaInMinutes: number = 3): boolean {
        let future = new Date();
        future = new Date(future.getTime() + (timedeltaInMinutes * 60 * 1000));
        return this.expiration(token) < future;
    }

    private tokenIsFresh(): boolean {
        return (this.currentApiToken != null) && Boolean(this.tokenToJson(this.currentApiToken).fresh);
    }
}
