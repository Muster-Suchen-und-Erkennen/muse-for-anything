import { DialogService } from "aurelia-dialog";
import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject, bindable } from "aurelia-framework";
import { Router } from "aurelia-router";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";
import { ApiLink, isChangedApiObject, isDeletedApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NavigationLink } from "services/navigation-links";
import { ConfirmActionDialog } from "./confirm-action-dialog";

@autoinject
export class ActionLink {
    @bindable action: NavigationLink;

    dangerous: boolean = false;

    private api: BaseApiService;
    private events: EventAggregator;
    private dialogService: DialogService;
    private router: Router;

    constructor(baseApi: BaseApiService, events: EventAggregator, dialogService: DialogService, router: Router) {
        this.api = baseApi;
        this.events = events;
        this.dialogService = dialogService;
        this.router = router;
    }

    private isDangerous(action: NavigationLink): boolean {
        const link = action.apiLink;
        return link.rel.some(rel => rel === "danger" || rel === "permanent");
    }

    actionChanged(newAction: NavigationLink): void {
        this.dangerous = this.isDangerous(newAction);
    }

    performAction(): void {
        const action = this.action;
        if (this.isDangerous(action)) {
            this.dialogService.open({
                viewModel: ConfirmActionDialog,
                model: { action: action },
                lock: false,
            }).whenClosed((result) => {
                if (!result.wasCancelled && result.output?.confirm) {
                    this.submitAction(action);
                }
            });
        } else {
            this.submitAction(action);
        }
    }

    private submitAction(action: NavigationLink) {
        this.api.submitByApiLink(this.action.apiLink).then(result => {
            if (isChangedApiObject(result.data)) {
                this.events.publish(API_RESOURCE_CHANGES_CHANNEL, result.data.changed.resourceKey);
            }
            if (isDeletedApiObject(result.data)) {
                this.navigateToOtherResourceOnDelete(result.data.redirectTo);
            }
        });
    }

    private navigateToOtherResourceOnDelete(newResourceLink: ApiLink) {
        this.api.buildClientUrl(newResourceLink)
            .then(clientUrl => {
                this.router.navigate(`/explore/${clientUrl}`);
            });
    }
}
