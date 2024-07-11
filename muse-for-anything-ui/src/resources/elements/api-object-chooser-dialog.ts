import { DialogController } from "aurelia-dialog";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { autoinject, observable } from "aurelia-framework";
import { DIALOG_ROUTING_CHANNEL } from "resources/events";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";

@autoinject
export class ApiObjectChooserDialog {

    dialogTitle: string;

    baseApiLink: ApiLink;
    @observable() currentApiLink: ApiLink;

    referenceType: string;
    chosenReference: ApiLink;

    private domNode: Element;
    private api: BaseApiService;
    private controller: DialogController;
    private events: EventAggregator;

    private subscription: Subscription | null = null;

    constructor(element: Element, apiService: BaseApiService, controller: DialogController, events: EventAggregator) {
        this.domNode = element;
        this.api = apiService;
        this.controller = controller;
        this.events = events;
        this.subscribe();
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(DIALOG_ROUTING_CHANNEL, (data: { "source": Element, "link": ApiLink }) => {
            let parent = data.source;
            while (parent != null && parent !== this.domNode) {
                parent = parent.parentElement;
            }
            const newApiLink = data.link;
            if (parent === this.domNode) {
                this.currentApiLink = newApiLink;
            }
        });
    }

    detached() {
        this.subscription?.dispose();
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
            const baseApiLink = response.links.find(link => {
                if (link.resourceType !== model.referenceType) {
                    return false;
                }
                if (link.rel.some(rel => rel === "nav")) {
                    return true;
                }
                return false;
            });
            if (baseApiLink?.resourceKey?.["?item-count"] == null && !baseApiLink.rel.some(rel => rel === "page")) {
                this.baseApiLink = baseApiLink;
                this.currentApiLink = baseApiLink;
            } else {
                const overwriteKey = {
                    ...(baseApiLink.resourceKey ?? {}),
                    "?item-count": "10",
                };
                this.api.resolveLinkKey(overwriteKey, baseApiLink?.resourceType).then(links => {
                    const overwriteLink = links.find(link => ["collection", "page"].every(rel => link.rel.some(r => r === rel)));
                    this.baseApiLink = overwriteLink;
                    this.currentApiLink = overwriteLink;
                });
            }
        });
    }

    onClick(event: MouseEvent) {
        const linkElement = event.composedPath().find(element => (element as Element).tagName === "A") as HTMLAnchorElement;
        console.log(event, event.defaultPrevented, linkElement)
        if (linkElement != null) {
            event.preventDefault();
            const clientUrl = linkElement.pathname + linkElement.search;
            if (!clientUrl.startsWith("/explore/")) {
                return;
            }
            this.api.resolveClientUrl(clientUrl.substring(9)).then(newApiLink => {
                if (newApiLink?.resourceKey?.["?item-count"] == null && !newApiLink.rel.some(rel => rel === "page")) {
                    this.currentApiLink = newApiLink;
                } else {
                    const overwriteKey = {
                        ...(newApiLink.resourceKey ?? {}),
                        "?item-count": "10",
                    };
                    this.api.resolveLinkKey(overwriteKey, newApiLink?.resourceType).then(links => {
                        this.currentApiLink = links.find(link => ["collection", "page"].every(rel => link.rel.some(r => r === rel)));
                    });
                }
            });
            return false;
        }
        // allow other event handlers to consume this event
        return true;
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
