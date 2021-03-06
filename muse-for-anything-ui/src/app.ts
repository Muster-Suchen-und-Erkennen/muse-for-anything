import { autoinject } from "aurelia-framework";
import { PLATFORM } from "aurelia-pal";
import { RouterConfiguration, Router } from "aurelia-router";

import { BaseApiService } from "rest/base-api";

@autoinject
export class App {
    public message = "Hello World!";

    private router: Router;

    constructor(baseApi: BaseApiService) {
        // query api by rel
        // baseApi.getByRel("authentication").then(result => console.log(result));
        // search api for rel
        // baseApi.searchResolveRels(["login", "post"]).then(result => console.log(result));
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
                nav: true,
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
        console.log(router.navigation)
    }
}
