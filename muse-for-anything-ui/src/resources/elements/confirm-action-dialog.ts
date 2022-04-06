import { bindable, autoinject, observable } from "aurelia-framework";
import { DialogController } from "aurelia-dialog";
import { ApiLink } from "rest/api-objects";
import { AuthenticationService } from "rest/authentication-service";
import { NavigationLink } from "services/navigation-links";

@autoinject
export class ConfirmActionDialog {

    @observable action: NavigationLink | null = null;

    actionType: "unknown" | "change" | "delete" = "unknown";
    isPermanent: boolean = false;

    private controller: DialogController;

    constructor(controller: DialogController) {
        this.controller = controller;
    }

    activate(model): void {
        this.action = model?.action ?? null;
    }

    actionChanged(newAction: NavigationLink | null): void {
        if (newAction == null) {
            this.actionType = "unknown";
            this.isPermanent = false;
            return;
        }
        if (newAction.apiLink.rel.some(rel => rel === "delete")) {
            this.actionType = "delete";
        } else if (newAction.apiLink.rel.some(rel => rel === "update")) {
            this.actionType = "change";
        } else {
            this.actionType = "unknown";
        }
        this.isPermanent = newAction.apiLink.rel.some(rel => rel === "permanent");
    }

    confirm(): void {
        this.controller.ok({
            confirm: true,
        });
    }

    cancel(): void {
        this.controller.cancel({
            confirm: false,
        });
    }
}
