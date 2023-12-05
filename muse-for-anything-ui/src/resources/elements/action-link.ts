import { DialogService } from "aurelia-dialog";
import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject, bindable } from "aurelia-framework";
import { Router } from "aurelia-router";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";
import { ApiLink, isChangedApiObject, isDeletedApiObject, isFileExportData } from "rest/api-objects";
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

    /**
     * Checks if the given NavigationLink is an export action.
     * @param action The NavigationLink to check.
     * @returns True if the NavigationLink is an export action, false otherwise.
     */
    private isExport(action: NavigationLink): boolean {
        const link = action.apiLink;
        return link.rel.some(rel => rel === "export");
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

    /**
     * Submits the given action by calling the API and handles the response accordingly.
     * If the API response indicates a changed resource, it publishes the resource key to the API_RESOURCE_CHANGES_CHANNEL.
     * If the API response indicates a deleted resource, it navigates to the specified redirect URL.
     * If the action is an export action and the API response contains file export data, it triggers a file download.
     * @param action The action to be submitted.
     */
    private submitAction(action: NavigationLink) {
        this.api.submitByApiLink(this.action.apiLink).then(result => {
            if (isChangedApiObject(result.data)) {
                this.events.publish(API_RESOURCE_CHANGES_CHANNEL, result.data.changed.resourceKey);
            }
            if (isDeletedApiObject(result.data)) {
                this.navigateToOtherResourceOnDelete(result.data.redirectTo);
            }
            if (this.isExport(action) && isFileExportData(result.data)) {
                const blob = new Blob([result.data.data], { type: 'application/xml' })
                const link = document.createElement('a');
                link.href = window.URL.createObjectURL(blob);
                link.download = result.data.name;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
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

