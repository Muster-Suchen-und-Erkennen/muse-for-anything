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
}
