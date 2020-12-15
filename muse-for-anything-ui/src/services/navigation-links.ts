import { autoinject } from "aurelia-framework";
import { EventAggregator } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiResponse, isApiObject } from "rest/api-objects";
import { NAV_LINKS_CHANNEL } from "resources/events";

export interface NavigationLink {
    clientUrl: string;
    title: string;
    sortKey: number;
    icon?: string;
    actionType?: "create" | "update" | "delete" | "restore";
    apiLink?: ApiLink;
}

export interface NavLinks {
    self?: NavigationLink;
    up?: NavigationLink;
    actions?: NavigationLink[];
}

const ACTION_RELS: Set<string> = new Set<string>(["create", "update", "delete", "restore"]);

@autoinject
export class NavigationLinksService {

    private events: EventAggregator;
    private api: BaseApiService;

    private mainApiResponse: NavLinks = {};

    // consolidated nav links
    private currentNavLinks: NavLinks = {};

    constructor(baseApi: BaseApiService, events: EventAggregator) {
        this.api = baseApi;
        this.events = events;
    }

    private updateNavLinksFromMainResponse(navLinks: NavLinks) {
        if (navLinks?.actions?.length >= 0) {
            navLinks.actions = navLinks.actions.sort((a, b) => a.sortKey - b.sortKey);
        }
        if (navLinks?.actions?.length === 0) {
            delete navLinks.actions;
        }
        this.mainApiResponse = navLinks;
        this.updateNavLinks();
    }

    private updateNavLinks() {
        // TODO consolidate nav links
        this.currentNavLinks = this.mainApiResponse;
        // send update event
        this.events.publish(NAV_LINKS_CHANNEL, this.currentNavLinks);
    }

    public getCurrentNavLinks(): NavLinks {
        return this.currentNavLinks;
    }

    private getTranslationKeyForLink(link: ApiLink): string {
        if (link.rel.some(rel => rel === "page" || rel === "collection")) {
            return `collection.${link.resourceType}`;
        }
        return link.resourceType;
    }

    public setMainApiResponse(response: ApiResponse<unknown>) {
        const navLinks: NavLinks = {};
        const actions: NavigationLink[] = [];
        navLinks.actions = actions;

        if (response == null) {
            this.updateNavLinksFromMainResponse(navLinks);
            return;
        }

        const promises: Array<Promise<unknown>> = [];

        let selfLink: ApiLink = null;
        if (isApiObject(response.data)) {
            selfLink = response.data.self;
            promises.push(this.api.buildClientUrl(selfLink).then(clientUrl => {
                navLinks.self = {
                    clientUrl: `/explore/${clientUrl}`,
                    title: `nav.${this.getTranslationKeyForLink(selfLink)}`,
                    apiLink: selfLink,
                    sortKey: 0,
                };
            }));
        }

        response.links.forEach(link => {
            // UP link
            if (link.rel.some(rel => rel === "up")) {
                promises.push(this.api.buildClientUrl(link).then(clientUrl => {
                    navLinks.up = {
                        clientUrl: `/explore/${clientUrl}`,
                        title: `nav.${this.getTranslationKeyForLink(link)}`,
                        apiLink: link,
                        sortKey: 10,
                    };
                }));
            }

            // action links
            if (link.rel.some(rel => ACTION_RELS.has(rel))) {
                let baseSortKey: number = 0;
                if (selfLink != null && link.resourceType !== selfLink.resourceType) {
                    // sort actions for other resource types behind actions for the current resource type
                    baseSortKey += 100;
                }
                promises.push(this.api.buildClientUrl(link).then(clientUrl => {
                    const navLinkBase = {
                        apiLink: link,
                    };

                    if (link.rel.some(rel => rel === "create")) {
                        actions.push({
                            ...navLinkBase,
                            clientUrl: `/create/${link.resourceType}/at/${clientUrl}`,
                            title: `nav.create.${this.getTranslationKeyForLink(link)}`,
                            sortKey: baseSortKey + 10,
                            actionType: "create",
                        });
                    }
                    if (link.rel.some(rel => rel === "update")) {
                        actions.push({
                            ...navLinkBase,
                            clientUrl: `/update/${link.resourceType}/at/${clientUrl}`,
                            title: `nav.update.${this.getTranslationKeyForLink(link)}`,
                            sortKey: baseSortKey + 20,
                            actionType: "update",
                        });
                    }
                    if (link.rel.some(rel => rel === "delete")) {
                        actions.push({
                            ...navLinkBase,
                            clientUrl: `/delete/${clientUrl}`,
                            title: `nav.delete.${this.getTranslationKeyForLink(link)}`,
                            sortKey: baseSortKey + 30,
                            actionType: "delete",
                        });
                    }
                    if (link.rel.some(rel => rel === "restore")) {
                        actions.push({
                            ...navLinkBase,
                            clientUrl: `/restore/${clientUrl}`,
                            title: `nav.restore.${this.getTranslationKeyForLink(link)}`,
                            sortKey: baseSortKey + 40,
                            actionType: "restore",
                        });
                    }
                }));
            }
        });

        if (promises.length > 0) {
            Promise.all(promises).then(() => {
                this.updateNavLinksFromMainResponse(navLinks);
            });
        } else {
            this.updateNavLinksFromMainResponse(navLinks);
        }
    }

}
