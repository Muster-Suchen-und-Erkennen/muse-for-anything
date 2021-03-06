import { bindable, bindingMode, observable } from "aurelia-framework";
import { ItemDescription, NormalizedApiSchema } from "rest/schema-objects";

export class ArrayForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable context: any;
    @bindable valuePush: any[];
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any[];
    @bindable({ defaultBindingMode: bindingMode.twoWay }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    isNullable: boolean = false;

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
        this.isNullable = normalized.type.has("null");
        this.minItems = normalized.minItems;
        this.maxItems = normalized.maxItems;
        const currentLength = this.initialData?.length ?? this.value?.length ?? 0;


        while (currentLength > this.itemsValid.length) {
            this.itemsValid.push(null);
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
        this.updateSignal();
    }

    updateSignal() {
        window.setTimeout(() => {
            this.itemsValidChanged(this.itemsValid);
            this.itemsDirtyChanged(this.itemsDirty);
        }, 1);
    }

    itemsValidChanged(newValue: boolean[], oldValue?) {
        if (this.value == null) {
            this.valid = this.isNullable;
            return;
        }
        const valuesValid = newValue?.every((valid, i) => valid || (i >= this.value.length)) ?? false;
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

    actionSignalCallback(action: { actionType: string, key: number }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = [...this.value];
            newValue.splice(action.key, 1);
            this.value = newValue;
        } else {
            // TODO other actions
            console.log(action)
        }
    }


}
