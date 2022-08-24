import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject, observable } from "aurelia-framework";
import { PLATFORM } from "aurelia-pal";
import { Router, RouterConfiguration } from "aurelia-router";
import { ACTIVE_LINK_CHANNEL, ROOT_NAV_LINKS_CHANNEL } from "resources/events";
import { NavigationLink, NavigationLinksService } from "services/navigation-links";

@autoinject
export class App {
    public message = "Hello World!";

    private router: Router;

    rootNavLinks: NavigationLink[] = [];

    @observable activeLink: string | null = null;

    activeNavLink: NavigationLink | null;

    constructor(events: EventAggregator, navService: NavigationLinksService) {
        // query api by rel
        // baseApi.getByRel("authentication").then(result => console.log(result));
        // search api for rel
        // baseApi.searchResolveRels(["login", "post"]).then(result => console.log(result));
        events.subscribe(ROOT_NAV_LINKS_CHANNEL, (navLinks) => {
            this.rootNavLinks = navLinks;
            this.activeLinkChanged();
        });
        events.subscribe(ACTIVE_LINK_CHANNEL, (activeLink: string | null) => {
            if (activeLink?.includes("?")) {
                this.activeLink = activeLink.split("?")[0];
            } else {
                this.activeLink = activeLink;
            }
        });
        this.rootNavLinks = navService.getCurrentRootNavLinks(); // query service to init nav events
    }

    activeLinkChanged() {
        if (this.activeLink == null) {
            this.activeNavLink = null;
            return;
        }
        this.activeNavLink = this.rootNavLinks.find(link => link.clientUrl.startsWith(this.activeLink));
    }

    configureRouter(config: RouterConfiguration, router: Router): void {
        this.router = router;
        config.title = "titles.app";
        config.options.pushState = true;
        config.options.root = "/"; // FIXME parse this from html base tag
        config.map([
            {
                route: ["", "home"],
                name: "home",
                settings: {
                    icon: "home",
                },
                viewPorts: {
                    sidebar: { moduleId: PLATFORM.moduleName("main-app/elements/home-sidebar") },
                    content: { moduleId: PLATFORM.moduleName("main-app/elements/home-content") },
                },
                nav: true,
                title: "titles.home",
            },
            {
                route: ["explore", "explore/*path"],
                href: "explore/ont-namespace",
                name: "explore",
                settings: {
                    icon: "document-stack",
                },
                viewPorts: {
                    sidebar: { moduleId: PLATFORM.moduleName("main-app/elements/explore-sidebar") },
                    content: { moduleId: PLATFORM.moduleName("main-app/elements/explore-content") },
                },
                nav: false,
                title: "titles.explore",
            },
            {
                route: ["create/:resourceType/at/*path"],
                name: "create",
                viewPorts: {
                    sidebar: { moduleId: PLATFORM.moduleName("main-app/elements/create-sidebar") },
                    content: { moduleId: PLATFORM.moduleName("main-app/elements/create-content") },
                },
                nav: false,
            },
            {
                route: ["update/:resourceType/at/*path"],
                name: "create",
                viewPorts: {
                    sidebar: { moduleId: PLATFORM.moduleName("main-app/elements/update-sidebar") },
                    content: { moduleId: PLATFORM.moduleName("main-app/elements/update-content") },
                },
                nav: false,
            },
        ]);
        config.mapUnknownRoutes({ redirect: "home" });
    }
}
