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
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: any[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: any[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    @observable() value: any[] = [];

    showInfo: boolean = false;

    description: string = "";

    isNullable: boolean = false;

    itemSchemas: ItemDescription[] = [];

    minItems: number;
    maxItems: number;
    isTuple: boolean = false;
    uniqueItems: boolean = false;
    orderedItems: boolean = true;

    @observable() itemsValid: boolean[] = [];
    @observable() itemsDirty: boolean[] = [];

    toggleInfo() {
        this.showInfo = !this.showInfo;
        return false;
    }

    initialDataChanged(newValue, oldValue) {
        this.reloadItems();
    }

    valueInChanged(newValue) {
        if (newValue == null) {
            this.value = null;
        } else {
            this.value = [...newValue];
        }
        this.reloadItems();
    }

    onItemValueUpdate = (value, binding) => {
        this.valueChanged(this.value, null);
    };

    valueChanged(newValue, oldValue) {
        const newOutValue: any[] = [...(newValue ?? [])];
        const newValueIsDifferent = newOutValue.some((item, index) => {
            if (this.valueOut?.[index] !== item) {
                return true;
            }
            return false;
        });
        const hasLessItems = newOutValue.length < (this.valueOut?.length ?? 0);
        if (newValueIsDifferent || hasLessItems) {
            if (newValue == null && this.isNullable) {
                this.valueOut = null;
            } else {
                this.valueOut = newOutValue;
            }
        }
    }

    valueOutChanged(newValue) {
        this.itemsValidChanged(this.itemsValid);
        this.itemsDirtyChanged(this.itemsDirty);
    }

    schemaChanged(newValue, oldValue) {
        this.reloadItems();
    }

    // eslint-disable-next-line complexity
    reloadItems() {
        if (this.schema == null) {
            this.description = "";
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            this.isTuple = false;
            this.uniqueItems = false;
            this.orderedItems = true;
            this.itemsValid = [];
            this.itemsDirty = [];
            this.valid = false;
            return;
        }
        const normalized = this.schema.normalized;
        this.description = normalized.description ?? "";
        if (normalized.type == null || !normalized.type.has("array")) {
            //console.error("Not an array!", this.schema); // FIXME better error!
            // can happen when switching type schema...
            this.itemSchemas = [];
            this.minItems = null;
            this.maxItems = 0;
            this.isTuple = false;
            this.uniqueItems = false;
            this.orderedItems = true;
            return;
        }
        this.isNullable = normalized.type.has("null");
        this.minItems = normalized.minItems;
        this.maxItems = normalized.maxItems;
        this.isTuple = Boolean(normalized.tupleItems);
        this.uniqueItems = normalized.uniqueItems;
        this.orderedItems = !normalized.unorderedItems;
        const currentValueLength = this.value?.length ?? 0;
        const initialDataLength = this.initialData?.length ?? 0;
        const currentLength = (currentValueLength > initialDataLength) ? currentValueLength : initialDataLength;


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
        this.valueChanged(this.value, null);
    }

    onItemValidUpdate = (value, binding) => {
        this.itemsValidChanged(this.itemsValid, null);
    };

    itemsValidChanged(newValue: boolean[], oldValue?) {
        if (this.valueOut == null) {
            this.valid = this.isNullable;
            return;
        }
        const valuesValid = newValue?.every((valid, i) => valid || (i >= this.valueOut.length)) ?? false;
        const minItemsValid = (this.minItems ?? 0) <= (newValue?.length ?? 0);
        const maxItemsValid = this.maxItems == null || this.maxItems >= (newValue?.length ?? 0);
        // TODO unique items
        this.valid = valuesValid && minItemsValid && maxItemsValid;
    }

    onItemDirtyUpdate = (value, binding) => {
        this.itemsDirtyChanged(this.itemsDirty, null);
    };

    itemsDirtyChanged(newValue: boolean[], oldValue?) {
        this.dirty = newValue?.some(valid => valid) ?? false;
    }

    addItem() {
        const newValue = [...(this.value ?? [])];
        newValue.push(null);
        this.value = newValue;
        this.reloadItems();
    }

    actionSignalCallback(action: { actionType: string, key: number }) {
        if (action.actionType === "remove" && this.value[action.key] !== undefined) {
            const newValue = [...this.value];
            newValue.splice(action.key, 1);
            this.value = newValue;
            this.reloadItems();
        } else {
            // TODO other actions
            console.log(action)
        }
    }


}
