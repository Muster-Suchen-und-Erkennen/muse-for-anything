import { EventAggregator } from "aurelia-event-aggregator";
import { autoinject } from "aurelia-framework";
import { THEME_CHANNEL, THEME_SETTING_CHANNEL } from "resources/events";


@autoinject
export class ThemeService {

    private events: EventAggregator;

    private storageKey: "M4A_THEME";

    private themeSetting: "light" | "dark" | "auto" = "auto";
    private activeTheme: "light" | "dark" = "light";

    constructor(events: EventAggregator) {
        this.events = events;
        this.loadThemeSettingFromStorage();
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", event => {
            this.updateActiveTheme();
        });
    }

    private loadThemeSettingFromStorage() {
        const oldThemeSetting = this.themeSetting;
        const newThemeSetting = localStorage.getItem(this.storageKey)?.toLowerCase() ?? "auto";
        if (newThemeSetting === "auto") {
            this.themeSetting = "auto";
        } else if (newThemeSetting === "light") {
            this.themeSetting = "light";
        } else if (newThemeSetting === "dark") {
            this.themeSetting = "dark";
        } else {
            this.themeSetting = "auto"; // catch all
        }
        if (this.themeSetting !== oldThemeSetting) {
            this.events.publish(THEME_SETTING_CHANNEL, this.themeSetting);
        }
        this.updateActiveTheme();
    }

    private updateActiveTheme() {
        const oldActiveTheme = this.activeTheme;
        if (this.themeSetting === "auto") {
            if (window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? false) {
                this.activeTheme = "dark";
            } else {
                this.activeTheme = "light";
            }
        } else {
            this.activeTheme = this.themeSetting;
        }
        if (this.activeTheme !== oldActiveTheme) {
            this.events.publish(THEME_CHANNEL, this.activeTheme);
        }
    }

    public getActiveTheme() {
        return this.activeTheme;
    }

    public getThemeSetting() {
        return this.themeSetting;
    }

    public changeThemeSetting(newSetting?: "light" | "dark" | "auto") {
        const themeSetting = newSetting ?? "auto";
        if (themeSetting !== "auto") {
            localStorage.setItem(this.storageKey, themeSetting);
        } else {
            localStorage.removeItem(this.storageKey);
        }
        this.loadThemeSettingFromStorage();
    }

}
