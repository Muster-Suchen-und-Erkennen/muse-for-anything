import { Aurelia } from "aurelia-framework";
import { PLATFORM } from "aurelia-pal";
import { AppRouter } from "aurelia-router";
import { EventAggregator } from "aurelia-event-aggregator";
import { I18N, TCustomAttribute } from "aurelia-i18n";
import Backend from "i18next-xhr-backend";
import * as environment from "../config/environment.json";

// import grapheditor library to enable webcomponent
import "@ustutt/grapheditor-webcomponent";

export function configure(aurelia: Aurelia): void {
    aurelia.use
        .standardConfiguration()
        .plugin(PLATFORM.moduleName("aurelia-i18n"), (instance) => {
            const aliases = ["t", "i18n"];
            // add aliases for 't' attribute
            TCustomAttribute.configureAliases(aliases);

            // register backend plugin
            //instance.i18next.use(Backend.with(aurelia.loader));
            instance.i18next.use(Backend);


            // adapt options to your needs (see http://i18next.com/docs/options/)
            // make sure to return the promise of the setup method, in order to guarantee proper loading
            return instance.setup({
                backend: {                                  // <-- configure backend settings
                    loadPath: "./static/locales/{{lng}}/{{ns}}.json", // <-- XHR settings for where to get the files from
                },
                attributes: aliases,
                lng: "en",
                fallbackLng: "en",
                ns: ["translation"],
                defaultNS: "translation",
                skipTranslationOnMissingKey: true,
                debug: true,
            }).then(() => {
                const router = aurelia.container.get(AppRouter);
                router.transformTitle = title => instance.tr(title);

                const eventAggregator = aurelia.container.get(EventAggregator);
                eventAggregator.subscribe("i18n:locale:changed", () => {
                    router.updateTitle();
                });
            });
        })
        .plugin(PLATFORM.moduleName("aurelia-dialog"), config => {
            config.useDefaults();
            config.useCSS("");
        })
        .plugin(PLATFORM.moduleName('@bmaxtech/aurelia-loaders'))
        .feature(PLATFORM.moduleName("resources/index"));

    aurelia.use.developmentLogging(environment.debug ? "debug" : "warn");

    if (environment.testing) {
        aurelia.use.plugin(PLATFORM.moduleName("aurelia-testing"));
    }

    aurelia.start().then(() => aurelia.setRoot(PLATFORM.moduleName("app")));
}
