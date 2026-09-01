import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject } from "aurelia-framework";
import { ACTIVE_LINK_CHANNEL, AUTH_EVENTS_CHANNEL, NAV_LINKS_CHANNEL, ROOT_NAV_LINKS_CHANNEL } from "resources/events";
import { ApiLink, ApiResponse, isApiObject, matchesLinkRel } from "rest/api-objects";
import { AuthenticationService } from "rest/authentication-service";
import { BaseApiService } from "rest/base-api";

export interface NavigationLink {
    clientUrl: string;
    title: string;
    titleEnd?: string;
    name?: string;
    sortKey: number;
    icon?: string;
    actionType?: "create" | "update" | "delete" | "restore" | "export";
    apiLink?: ApiLink;
}

export interface NavLinks {
    self?: NavigationLink;
    up?: NavigationLink;
    actions?: NavigationLink[];
    nav?: NavigationLink[];
}

const ACTION_RELS: Set<string> = new Set<string>(["create", "update", "delete", "restore", "export"]);

export const RESOURCE_TYPE_ICONS: Map<string, string> = new Map([
    ["user", "user"],
    ["user-role", "user-role"],
    ["user-grant", "user-grant"],
    ["ont-namespace", "ont-namespace"],
    ["ont-object", "ont-object"],
    ["ont-object-version", "ont-object"],
    ["ont-type", "ont-type"],
    ["ont-type-version", "ont-type"],
    ["ont-taxonomy", "ont-taxonomy"],
    ["ont-taxonomy-item", "ont-taxonomy-item"],
    ["ont-taxonomy-item-version", "ont-taxonomy-item"],
    ["ont-taxonomy-item-relation", "ont-taxonomy-item-relation"],
]);

export const COLLECTION_RESOURCE_TYPE_ICONS: Map<string, string> = new Map([
    ["user", "users"],
    ["user-role", "user-roles"],
    ["user-grant", "user-grants"],
]);


@autoinject
export class NavigationLinksService {

    private events: EventAggregator;
    private auth: AuthenticationService;
    private api: BaseApiService;

    // root nav links
    private rootNavLinks: NavigationLink[] = [];

    // consolidated root nav links
    private currentRootNavLinks: NavigationLink[] = [];

    // nav links from the main active resource
    private mainApiResponse: NavLinks = {};

    // consolidated nav links
    private currentNavLinks: NavLinks = {};

    private currentActiveLink: string | null = null;

    constructor(baseApi: BaseApiService, auth: AuthenticationService, events: EventAggregator) {
        this.api = baseApi;
        this.auth = auth;
        this.events = events;
        this.updateRootNavLinks();
    }

    private setLinkIcon(navLink: NavigationLink, link: ApiLink) {
        if (link.rel.some(rel => rel === "collection")) {
            if (COLLECTION_RESOURCE_TYPE_ICONS.has(link.resourceType)) {
                navLink.icon = COLLECTION_RESOURCE_TYPE_ICONS.get(link.resourceType);
                return;
            }
        }
        if (RESOURCE_TYPE_ICONS.has(link.resourceType)) {
            navLink.icon = RESOURCE_TYPE_ICONS.get(link.resourceType);
        }
    }

    private updateRootNavLinks() {
        this.api.getRootNavigationLinks()
            .then(links => {
                return Promise.all(links.map(link => {
                    return this.api.buildClientUrl(link).then(clientUrl => {
                        const navLink: NavigationLink = {
                            clientUrl: `/explore/${clientUrl}`,
                            title: `nav.${this.getTranslationKeyForLink(link)}`,
                            apiLink: link,
                            sortKey: 0,
                        };
                        this.setLinkIcon(navLink, link);
                        if (link.name != null) {
                            navLink.name = link.name;
                        }
                        if (matchesLinkRel(link, ["ont-namespace", "collection"])) {
                            navLink.title = "titles.explore";
                            navLink.icon = "document-stack";
                        }
                        return navLink;
                    });
                }));
            })
            .then(resolvedLinks => {
                this.rootNavLinks = resolvedLinks.sort((a, b) => a.sortKey - b.sortKey);
                this.updateCurentRootNavLinks();
            })
            .then(() => {
                // update root nav links on auth state changes!
                this.events.subscribe(AUTH_EVENTS_CHANNEL, () => this.updateCurentRootNavLinks());
            });
    }

    private updateCurentRootNavLinks() {
        const isAuthenticated = this.auth.currentStatus?.isLoggedIn ?? false;
        const newRootNavLinks = this.rootNavLinks.filter((link) => {
            if (matchesLinkRel(link.apiLink, "authenticated") && !isAuthenticated) {
                return false;
            }
            return true;
        });
        if (this.currentRootNavLinks.length === newRootNavLinks.length && this.rootNavLinks.every((link, index) => this.currentRootNavLinks[index] === link)) {
            return; // nothing has changed
        }
        this.currentRootNavLinks = newRootNavLinks;
        this.events.publish(ROOT_NAV_LINKS_CHANNEL, this.currentRootNavLinks);
    }

    public getCurrentRootNavLinks(): NavigationLink[] {
        return this.currentRootNavLinks;
    }


    private updateNavLinksFromMainResponse(navLinks: NavLinks) {
        if (navLinks?.actions?.length >= 0) {
            navLinks.actions = navLinks.actions.sort((a, b) => a.sortKey - b.sortKey);
        }
        if (navLinks?.actions?.length === 0) {
            delete navLinks.actions;
        }
        if (navLinks?.nav?.length >= 0) {
            navLinks.nav = navLinks.nav.sort((a, b) => a.sortKey - b.sortKey);
        }
        if (navLinks?.nav?.length === 0) {
            delete navLinks.nav;
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
        if (link.rel.some(rel => rel === "outdated")) {
            return `outdated.${link.resourceType}`;
        }
        if (link.rel.some(rel => rel === "page" || rel === "collection")) {
            return `collection.${link.resourceType}`;
        }
        if (link.rel.some(rel => rel === "export")) {
            return link.rel.find(rel => rel.startsWith("ont-")) ?? link.resourceType;
        }
        return link.resourceType;
    }

    private updateCurrentActiveLink(newLink: string | null) {
        if (this.currentActiveLink !== newLink) {
            this.currentActiveLink = newLink;
            this.events.publish(ACTIVE_LINK_CHANNEL, this.currentActiveLink);
        }
    }

    public setMainApiResponse(response: ApiResponse<unknown>) {
        const navLinks: NavLinks = {};
        const actions: NavigationLink[] = [];
        const navigations: NavigationLink[] = [];
        navLinks.actions = actions;
        navLinks.nav = navigations;

        if (response == null) {
            this.updateNavLinksFromMainResponse(navLinks);
            this.updateCurrentActiveLink(null);
            return;
        }

        const promises: Array<Promise<unknown>> = [];

        let selfLink: ApiLink = null;
        if (isApiObject(response.data)) {
            selfLink = response.data.self;
            promises.push(this.api.buildClientUrl(selfLink).then(clientUrl => {
                this.updateCurrentActiveLink(`/explore/${clientUrl}`);
                navLinks.self = {
                    clientUrl: `/explore/${clientUrl}`,
                    title: `nav.${this.getTranslationKeyForLink(selfLink)}`,
                    apiLink: selfLink,
                    sortKey: 0,
                };
                this.setLinkIcon(navLinks.self, selfLink);
                if (selfLink.name != null) {
                    navLinks.self.name = selfLink.name;
                }
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
                    this.setLinkIcon(navLinks.up, link);
                    if (link.name != null) {
                        navLinks.up.name = link.name;
                    }
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
                    const navLinkBase: { apiLink: ApiLink, name?: string } = {
                        apiLink: link,
                    };

                    if (link.name != null) {
                        navLinkBase.name = link.name;
                    }

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
                    if (link.rel.some(rel => rel === "export")) {
                        actions.push({
                            ...navLinkBase,
                            clientUrl: `/export/${clientUrl}`,
                            title: `nav.export.${this.getTranslationKeyForLink(link)}`,
                            titleEnd: "nav.as-owl",
                            sortKey: baseSortKey + 50,
                            actionType: "export",
                        });
                    }
                }));
            }
            // action links
            if (link.rel.some(rel => rel === "nav")) {
                promises.push(this.api.buildClientUrl(link).then(clientUrl => {
                    const navLink: NavigationLink = {
                        apiLink: link,
                        clientUrl: `/explore/${clientUrl}`,
                        title: `nav.${this.getTranslationKeyForLink(link)}`,
                        sortKey: 10, // TODO better sort keys
                    };
                    this.setLinkIcon(navLink, link);
                    if (link.name != null) {
                        navLink.name = link.name;
                    }
                    navigations.push(navLink);
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
