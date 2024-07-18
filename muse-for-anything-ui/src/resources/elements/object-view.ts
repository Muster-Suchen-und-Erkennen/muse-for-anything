import { bindable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";

export class ObjectView {
    @bindable data: any;
    @bindable schema: NormalizedApiSchema;
    @bindable context: any;

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
        if (this.data == null) {
            return;
        }
        this.properties = this.schema.getPropertyList(Object.keys(this.data));
    }

    showPropertyTitle(schema: NormalizedApiSchema): boolean {
        if (schema?.normalized?.customType === "typeRoot") {
            return false; // hide the property title of the type root type properties
        }
        return true;
    }

    isObjectProperty(schema: NormalizedApiSchema): boolean {
        if (schema?.normalized?.mainType === "object") {
            if (schema.normalized?.customType != null) {
                // TODO maybe exclude some custom types
                if (schema.normalized.customType === "resourceReference") {
                    return false; // treat resource reference as a simple type
                }
                if (schema.normalized.customType === "typeRoot") {
                    return false; // treat resource reference as a simple type
                }
            }
            return true;
        }
        return false;
    }

    isArrayProperty(schema: NormalizedApiSchema): boolean {
        if (schema?.normalized?.mainType === "array") {
            if (schema.normalized?.customType != null) {
                // TODO maybe exclude some custom types
                if (schema.normalized.customType === "jsonType") {
                    return false; // treat json type arrays as a simple type
                }
            }
            return true;
        }
        return false;
    }

    propertyStyle(schema: NormalizedApiSchema): string {
        if (this.isObjectProperty(schema) || this.isArrayProperty(schema)) {
            return "flex-basis: 100%; margin-left: 0.5rem;";
        }
        return "";
    }
}
