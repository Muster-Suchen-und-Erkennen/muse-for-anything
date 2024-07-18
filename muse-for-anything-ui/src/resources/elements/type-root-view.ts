import { bindable } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";


interface TypeDescription {
    title: string;
    data: any;
    schema: NormalizedApiSchema | null;
}


export class TypeRootView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;
    @bindable context: any;

    contextOut: any;

    mainType: TypeDescription | null = null;

    embeddedTypes: TypeDescription[] = [];


    dataChanged(newValue, oldValue) {
        this.updateTypes();
        this.updateContext();
    }

    schemaChanged(newValue, oldValue) {
        this.updateTypes();
    }

    contextChanged(newValue, oldValue) {
        this.updateContext();
    }

    private updateContext() {
        const context = { ...(this.context ?? {}) };

        const topLevelTypeDefs = [];
        const defs = this.data?.definitions ?? {};
        Object.keys(defs).forEach(key => {
            topLevelTypeDefs.push({
                key: key,
                title: defs[key]?.title ?? key,
            });
        });
        context.topLevelTypeName = this.data?.title;
        context.topLevelTypeDefs = topLevelTypeDefs;

        if (
            this.contextOut == null ||
            context.topLevelTypeName !== this.contextOut.topLevelTypeName ||
            JSON.stringify(context.topLevelTypeDefs) !== JSON.stringify(this.contextOut.topLevelTypeDefs)
        ) {
            this.contextOut = context;
        }
    }

    // eslint-disable-next-line complexity
    updateTypes() {
        if (this.schema == null) {
            return;
        }
        if (this.data == null) {
            return;
        }
        const defs = this.data?.definitions ?? {};

        const embeddedTypeKeys = Object.keys(defs).filter(k => k !== "root");
        const allTypeKeys = ["root"].concat(embeddedTypeKeys);

        const defsSchema = this.schema.getPropertyList(["definitions"], { allowList: ["definitions"] })[0]?.propertySchema ?? null;

        const properties = defsSchema?.getPropertyList?.(allTypeKeys, { allowList: allTypeKeys }) ?? [];

        this.mainType = {
            data: defs.root ?? {},
            // eslint-disable-next-line no-ternary
            title: defs.root?.title ? `${defs.root?.title} (root)` : "root",
            schema: properties.find(p => p.propertyName === "root")?.propertySchema ?? null,
        };

        const embeddedTypes: TypeDescription[] = [];
        embeddedTypeKeys.forEach(key => {
            embeddedTypes.push({
                data: defs[key] ?? {},
                // eslint-disable-next-line no-ternary
                title: defs[key]?.title ? `${defs[key]?.title} (${key})` : key,
                schema: properties.find(p => p.propertyName === key)?.propertySchema ?? null,
            });
        });
        this.embeddedTypes = embeddedTypes;
    }
}
