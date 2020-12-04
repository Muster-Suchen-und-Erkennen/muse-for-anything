import { autoinject } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { NAV_LINKS_CHANNEL, NavLinks, NavigationLinksService } from "services/navigation-links";

const ACCEPTED_NAV_LINKS = new Set<string>(["up", "self"]);

@autoinject
export class CreateSidebar {

    isEmpty: boolean = true;
    navLinks: NavLinks = {};

    private events: EventAggregator;
    private subscription: Subscription;

    constructor(events: EventAggregator, navService: NavigationLinksService) {
        this.events = events;
        this.subscribe();
    }

    private updateNavLinks(navLinks: NavLinks) {
        this.navLinks = navLinks;
        this.isEmpty = !Object.keys(navLinks).some(key => ACCEPTED_NAV_LINKS.has(key));
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            this.updateNavLinks(navLinks);
        });
    }

    detached() {
        this.subscription?.dispose();
    }
}
