import { bindable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class BooleanForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable valuePush: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    isNullable: boolean = true;

    @child(".input-valid-check") formInput: Element;

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined && !this.dirty) {
            if (this.isNullable) {
                this.value = newValue;
            } else {
                this.value = newValue ?? false;
            }
            this.dirty = false;
        }
    }

    valuePushChanged(newValue, oldValue) {
        if (this.value === newValue) {
            return;
        }
        this.value = newValue;
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.type.has(null) || !this.required;
        if (!this.isNullable && this.value == null) {
            this.value = false;
        }
    }

    cycle(event?: Event) {
        if (this.isNullable) {
            if (this.value) {
                this.value = null;
                return;
            }
        }
        if (this.value == null) {
            this.value = false;
            return;
        }
        if (this.value) {
            this.value = false;
        } else {
            this.value = true;
        }
        if (event) {
            // TODO clicking on checkbox cannot change its state...
        }
    }

    // eslint-disable-next-line complexity
    valueChanged(newValue, oldValue) { // TODO value does not change for float input with integer type
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue === ""));
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateCheckbox();

        this.valid = this.isNullable || newValue != null;
    }

    formInputChanged() {
        this.updateCheckbox();
    }

    updateCheckbox() {
        const input = this.formInput as HTMLInputElement;
        if (input != null) {
            if (this.value == null) {
                input.checked = false;
                input.indeterminate = true;
                console.log("reset", input.checked, input.indeterminate);
                return;
            }
            input.checked = this.value;
            input.indeterminate = false;
            console.log("update", this.value, input.checked, input.indeterminate)
        }
    }

}
