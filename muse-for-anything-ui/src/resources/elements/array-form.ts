import { bindable, bindingMode, children, child, observable } from "aurelia-framework";
import { ItemDescription, NormalizedApiSchema } from "rest/schema-objects";
import { SchemaValueObserver } from "./schema-value-observer";

export class ArrayForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable debug: boolean = false;
    @bindable valuePush: any[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: any[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    itemSchemas: ItemDescription[] = [];

    minItems: number;
    maxItems: number;

    invalidItems: Set<number> = new Set();
    validItems: Set<number> = new Set();

    valueObserver: SchemaValueObserver = {
        onValueChanged: (key, newValue, oldValue) => {
            this.itemChanged(key as number, newValue);
        },
        onValidityChanged: (key, newValue, oldValue) => {
            this.itemValidityChanged(key as number, newValue);
        },
    };

    initialDataChanged(newValue, oldValue) {
        this.reloadItems();
    }

    valuePushChanged(newValue, oldValue) {
        if (this.value === newValue) {
            return;
        }
        this.value = newValue;
        this.reloadItems();
    }

    schemaChanged(newValue, oldValue) {
        this.invalidItems = new Set();
        this.validItems = new Set();
        this.valid = null;
        this.reloadItems();
    }

    reloadItems() {
        if (this.schema == null) {
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            return;
        }
        const normalized = this.schema.normalized;
        if (!normalized.type.has("array")) {
            console.error("Not an array!", this.schema); // FIXME better error!
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            return;
        }
        this.minItems = normalized.minItems;
        this.maxItems = normalized.maxItems;
        const currentLength = this.initialData?.length ?? this.value?.length ?? 0;

        this.itemSchemas = this.schema.getItemList(currentLength);
    }

    addItem() {
        const newValue = [...(this.value ?? [])];
        newValue.push(null);
        this.valuePush = newValue;
    }

    itemChanged(key: number, newValue) {
        if (this.value != null && this.value[key] === newValue) {
            return;
        }
        console.log("item changed", key, newValue)
        if (key > (this.minItems ?? 0) && newValue == null) {
            // if key is not required then remove it if value is null
            const tmpValue = [];
            this.value.forEach((val, i) => {
                if (i === key) {
                    return;
                }
                tmpValue.push(val);
            });
            // TODO test if this actually works (or loops)
            // this.value = newValue;
            return;
        }
        if (this.value[key] == null && newValue == null) {
            return;
        }
        const tmpValue = [...this.value];
        tmpValue[key] = newValue;
        this.value = tmpValue;
    }

    itemValidityChanged(key: number, newValue) {
        if (newValue) {
            this.invalidItems.delete(key);
            this.validItems.add(key);
        } else {
            this.invalidItems.add(key);
            this.validItems.delete(key);
        }
        const knownProps = this.invalidItems.size + this.validItems.size;
        if (knownProps < this.itemSchemas.length) {
            // valid status not known for all props
            this.valid = (this.invalidItems.size > 0) ? true : null;
        } else {
            this.valid = this.invalidItems.size === 0;
        }
    }
}
