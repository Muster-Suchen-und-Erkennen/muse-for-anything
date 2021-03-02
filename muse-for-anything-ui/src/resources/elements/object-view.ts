import { bindable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";

export class ObjectView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;

    properties: PropertyDescription[] = [];

    dataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    schemaChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    reloadProperties() {
        if (this.schema == null) {
            this.properties = [];
            return;
        }
        if (!this.schema.normalized.type.has("object")) {
            console.error("Not an object!"); // FIXME better error!
            this.properties = [];
            return;
        }
        this.properties = this.schema.getPropertyList(Object.keys(this.data));
    }

    isObjectProperty(schema: NormalizedApiSchema): boolean {
        if (schema?.normalized?.mainType === "object") {
            if (schema.normalized?.customType != null) {
                // TODO maybe exclude some custom types
            }
            return true;
        }
        return false;
    }

    isArrayProperty(schema: NormalizedApiSchema): boolean {
        return schema?.normalized?.mainType === "array";
    }

    propertyStyle(schema: NormalizedApiSchema): string {
        if (this.isObjectProperty(schema) || this.isArrayProperty(schema)) {
            return "flex-basis: 100%; margin-left: 0.5rem;";
        }
        return "";
    }
}
