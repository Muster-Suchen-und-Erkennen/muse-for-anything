import { bindable, autoinject, observable } from "aurelia-framework";
import { DialogController } from "aurelia-dialog";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";

@autoinject
export class ApiObjectChooserDialog {

    dialogTitle: string;

    baseApiLink: ApiLink;
    @observable() currentApiLink: ApiLink;

    referenceType: string;
    chosenReference: ApiLink;

    private api: BaseApiService;
    private controller: DialogController;

    constructor(apiService: BaseApiService, controller: DialogController) {
        this.api = apiService;
        this.controller = controller;
    }

    currentApiLinkChanged(newLink: ApiLink) {
        this.chosenReference = null;
        if (newLink.resourceType === this.referenceType) {
            if (newLink.rel.some(rel => rel === "collection")) {
                return;
            }
            // reference matches
            this.chosenReference = newLink;
        }
    }

    activate(model) {
        this.referenceType = model?.referenceType;
        if (model?.referenceType == null || model?.baseApiLink == null) {
            return;
        }
        this.api.getByApiLink(model.baseApiLink).then(response => {
            this.baseApiLink = response.links.find(link => {
                if (link.resourceType !== model.referenceType) {
                    return false;
                }
                if (link.rel.some(rel => rel === "nav")) {
                    return true;
                }
                return false;
            });
            this.currentApiLink = this.baseApiLink;
        });
    }

    onClick(event: MouseEvent) {
        const linkElement = event.composedPath().find(element => (element as Element).tagName === "A") as HTMLAnchorElement;
        if (linkElement != null) {
            event.preventDefault();
            const clientUrl = linkElement.pathname;
            if (!clientUrl.startsWith("/explore/")) {
                return;
            }
            this.api.resolveClientUrl(clientUrl.substring(9)).then(newApiLink => {
                this.currentApiLink = newApiLink;
            });
            return false;
        }
    }

    navigateBack() {
        this.currentApiLink = this.baseApiLink;
    }

    confirm() {
        if (this.chosenReference != null) {
            this.controller.ok(this.chosenReference);
        }
    }
}
