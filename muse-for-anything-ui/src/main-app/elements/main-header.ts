import { bindable, observable, autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { DialogCloseResult, DialogService } from "aurelia-dialog";
import { LoginDialog } from "../../resources/elements/login-dialog";
import { AuthenticationService, LOGIN, LOGIN_EXPIRED, LOGIN_EXPIRES_SOON, LOGOUT } from "../../rest/authentication-service";
import { AUTH_EVENTS_CHANNEL } from "resources/events";


@autoinject()
export class MainHeader {

    isLoggedIn: boolean = false;

    private dialogService: DialogService;
    private authService: AuthenticationService;
    private events: EventAggregator;

    private subscription: Subscription;

    constructor(dialogService: DialogService, authService: AuthenticationService, events: EventAggregator) {
        this.dialogService = dialogService;
        this.authService = authService;
        this.events = events;
        this.isLoggedIn = this.authService.currentStatus.isLoggedIn;
        this.subscribe();
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
