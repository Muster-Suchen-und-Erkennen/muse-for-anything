import { bindable, autoinject, observable } from "aurelia-framework";
import { DialogController } from "aurelia-dialog";
import { ApiLink } from "rest/api-objects";
import { AuthenticationService } from "rest/authentication-service";

@autoinject
export class LoginDialog {

    @observable username: string;
    @observable password: string;
    @observable keepLogin: boolean = false;

    usernameValid: boolean = false;
    passwordValid: boolean = false;

    usernameDirty: boolean = false;
    passwordDirty: boolean = false;

    title: string = "titles.login";
    confirmTitle: string = "login.confirm-login";
    isPasswordOnly: boolean = false;

    private auth: AuthenticationService;
    private controller: DialogController;

    constructor(authService: AuthenticationService, controller: DialogController) {
        this.auth = authService;
        this.controller = controller;
    }

    usernameChanged(newUsername: string) {
        this.usernameValid = newUsername != null && newUsername.length >= 3;
    }

    passwordChanged(newPassword: string) {
        this.passwordValid = newPassword != null && newPassword.length >= 3;
    }

    activate(model) {
        if (model?.isPasswordOnly) {
            this.isPasswordOnly = true;
            if (model.username != null) {
                this.username = this.username;
            }
            this.usernameValid = true;
        }
        if (model?.title != null) {
            this.title = model.title;
        }
        if (model.confirmTitle != null) {
            this.confirmTitle = model.confirmTitle
        }
    }

    confirm() {
        if (this.usernameValid && this.passwordValid) {
            this.controller.ok({
                username: this.username,
                password: this.password,
                keepLogin: this.keepLogin,
            });
        }
    }
}
