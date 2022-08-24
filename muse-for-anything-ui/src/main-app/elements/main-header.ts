import { DialogCloseResult, DialogService } from "aurelia-dialog";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { autoinject } from "aurelia-framework";
import { AUTH_EVENTS_CHANNEL } from "resources/events";
import { BaseApiService } from "rest/base-api";
import { LoginDialog } from "../../resources/elements/login-dialog";
import { AuthenticationService, LOGIN, LOGIN_EXPIRED, LOGIN_EXPIRES_SOON, LOGOUT } from "../../rest/authentication-service";


@autoinject()
export class MainHeader {

    isLoggedIn: boolean = false;

    private dialogService: DialogService;
    private authService: AuthenticationService;
    private api: BaseApiService;
    private events: EventAggregator;

    private subscription: Subscription;

    constructor(dialogService: DialogService, authService: AuthenticationService, api: BaseApiService, events: EventAggregator) {
        this.dialogService = dialogService;
        this.authService = authService;
        this.api = api;
        this.events = events;
        this.isLoggedIn = this.authService.currentStatus.isLoggedIn;
        this.subscribe();
    }

    /**
     * Helper function reloading everything bypassing the cache.
     *
     * TODO remove once caching can detect stale entries (e.g. via etags)
     */
    public reload() {
        this.api.clearCaches(true).then(() => {
            window.location.reload();
        });
    }

    public logout() {
        this.authService.logout();
    }

    public showLoginDialog() {
        // TODO check login status
        const model = {};
        const onClose = (response: DialogCloseResult) => {
            if (!response.wasCancelled) {
                this.handleLogin(response.output);
            } else {
                // do nothing on cancel
            }
        }
        this.openDialog(model, onClose);
    }

    private openDialog(model: { isPasswordOnly?: boolean, title?: string, confirmTitle?: string }, onClose: (response: DialogCloseResult) => any) {
        this.dialogService.open({ viewModel: LoginDialog, model: model, lock: false }).whenClosed(onClose);
    }

    private handleLogin(loginData: { username: string, password: string, keepLogin: boolean }) {
        this.authService.login(loginData.username, loginData.password, loginData.keepLogin);
    }

    private subscribe() {
        this.subscription = this.events.subscribe(AUTH_EVENTS_CHANNEL, (authEvent: string) => {
            console.log(authEvent)
            if (authEvent == LOGIN_EXPIRES_SOON) {
                // TODO
            }
            if (authEvent == LOGIN_EXPIRED) {
                // TODO
            }
            if (authEvent == LOGIN) {
                this.isLoggedIn = true;
            }
            if (authEvent == LOGOUT) {
                this.isLoggedIn = false;
            }
        });

    }

    detached() {
        this.subscription?.dispose();
    }
}
