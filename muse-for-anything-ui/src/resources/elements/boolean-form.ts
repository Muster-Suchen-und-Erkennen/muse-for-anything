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
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
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

    valueChanged(newValue, oldValue) {
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
        // TODO update only works when checkbox is not directly clicked
        const input = this.formInput as HTMLInputElement;
        if (input != null) {
            if (this.value == null) {
                input.checked = false;
                input.indeterminate = true;
                return;
            }
            input.checked = this.value;
            input.indeterminate = false;
        }
    }

}
