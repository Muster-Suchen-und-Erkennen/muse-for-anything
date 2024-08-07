import { FrameworkConfiguration } from 'aurelia-framework';
import { PLATFORM } from "aurelia-pal";

export function configure(config: FrameworkConfiguration): void {
    config.globalResources([
        PLATFORM.moduleName("resources/value-converters/find"),
        PLATFORM.moduleName("resources/value-converters/json"),
        PLATFORM.moduleName("resources/value-converters/number"),
        PLATFORM.moduleName("resources/binding-behaviors/optional"),
        PLATFORM.moduleName("resources/binding-behaviors/empty"),
        PLATFORM.moduleName("resources/binding-behaviors/tee"),
        PLATFORM.moduleName("resources/binding-behaviors/view-signal"),
    ]);
}
