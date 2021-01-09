import { bindable, bindingMode, observable } from "aurelia-framework";
import { ItemDescription, NormalizedApiSchema } from "rest/schema-objects";

export class ArrayForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable debug: boolean = false;
    @bindable valuePush: any[];
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any[];
    @bindable({ defaultBindingMode: bindingMode.twoWay }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    itemSchemas: ItemDescription[] = [];

    minItems: number;
    maxItems: number;

    @observable() itemsValid: boolean[] = [];
    @observable() itemsDirty: boolean[] = [];

    initialDataChanged(newValue, oldValue) {
        this.reloadItems();
    }

    valueChanged(newValue, oldValue) {
        this.reloadItems();
    }

    schemaChanged(newValue, oldValue) {
        this.reloadItems();
    }

    reloadItems() {
        if (this.schema == null) {
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            this.itemsValid = [];
            this.itemsDirty = [];
            this.valid = false;
            return;
        }
        const normalized = this.schema.normalized;
        if (normalized.type == null || !normalized.type.has("array")) {
            //console.error("Not an array!", this.schema); // FIXME better error!
            // can happen when switching type schema...
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            return;
        }
        this.minItems = normalized.minItems;
        this.maxItems = normalized.maxItems;
        const currentLength = this.initialData?.length ?? this.value?.length ?? 0;


        while (currentLength > this.itemsValid.length) {
            this.itemsValid.push(false);
        }
        while (currentLength > this.itemsDirty.length) {
            this.itemsDirty.push(false);
        }
        if (currentLength < this.itemsValid.length) {
            this.itemsValid = this.itemsValid.slice(0, currentLength);
        }
        if (currentLength < this.itemsDirty.length) {
            this.itemsDirty = this.itemsDirty.slice(0, currentLength);
        }

        this.itemSchemas = this.schema.getItemList(currentLength);
    }

    updateSignal() {
        this.itemsValidChanged(this.itemsValid);
        this.itemsDirtyChanged(this.itemsDirty);
    }

    itemsValidChanged(newValue: boolean[], oldValue?) {
        const valuesValid = newValue?.every(valid => valid) ?? false;
        const minItemsValid = (this.minItems ?? 0) <= (newValue?.length ?? 0);
        const maxItemsValid = this.maxItems == null || this.maxItems >= (newValue?.length ?? 0);
        // TODO unique items
        this.valid = valuesValid && minItemsValid && maxItemsValid;
    }

    itemsDirtyChanged(newValue: boolean[], oldValue?) {
        this.dirty = newValue?.some(valid => valid) ?? false;
    }

    addItem() {
        const newValue = [...(this.value ?? [])];
        newValue.push(null);
        this.value = newValue;
    }


}
