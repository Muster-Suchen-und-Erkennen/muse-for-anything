import { bindable } from "aurelia-framework";
import { ItemDescription, NormalizedApiSchema } from "rest/schema-objects";

export class ArrayView {
    @bindable data: any[];
    @bindable schema: NormalizedApiSchema;

    items: ItemDescription[] = [];

    dataChanged(newValue, oldValue) {
        this.reloadItems();
    }

    schemaChanged(newValue, oldValue) {
        this.reloadItems();
    }

    reloadItems() {
        if (this.schema == null) {
            this.items = [];
            return;
        }
        if (!this.schema.normalized.type.has("array")) {
            console.error("Not an array!"); // FIXME better error!
            this.items = [];
            return;
        }
        this.items = this.schema.getItemList(this.data?.length ?? 0);
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
