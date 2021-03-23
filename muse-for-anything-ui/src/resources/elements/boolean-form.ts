import { bindable, observable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class BooleanForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: boolean | null;

    slug = nanoid(8);

    isNullable: boolean = true;

    @child(".input-valid-check") formInput: Element;

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            this.value = newValue;
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.type.has(null);
        if (!this.isNullable && this.value == null) {
            this.value = false;
        }
        this.updateValid();
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

    valueInChanged(newValue) {
        this.value = newValue;
    }

    valueChanged(newValue, oldValue) {
        this.updateCheckbox();
        if (this.isNullable) {
            this.valueOut = newValue;
        } else {
            this.valueOut = newValue ?? false;
        }
    }

    valueOutChanged(newValue) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue === false));
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateValid();

    }

    updateValid() {
        this.valid = this.isNullable || this.value != null;
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
