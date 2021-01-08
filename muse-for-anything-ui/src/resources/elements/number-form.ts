import { bindable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class NumberForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable valuePush: number;
    @bindable({ defaultBindingMode: bindingMode.fromView }) value: number;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    formIsValid: boolean = false;
    boundsValid: boolean = true;
    stepValid: boolean = true;

    isNullable: boolean = true;

    isInteger: boolean = true;

    step: number = 0.1;

    minimum: number;
    maximum: number;

    exclusiveMinimum: number;
    exclusiveMaximum: number;

    extraMultiples: number[];

    @child(".input-valid-check") formInput: Element;

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined && !this.dirty) {
            if (this.isNullable) {
                this.value = newValue;
            } else {
                this.value = newValue ?? 0;
            }
            this.dirty = false;
        }
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
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
            this.value = 0;
        }

        if (normalized.mainType === "integer") {
            this.step = 1;
            this.isInteger = true;
        } else {
            this.step = 0;
            this.isInteger = false;
        }

        this.minimum = normalized.minimum ?? normalized.exclusiveMinimum;
        this.maximum = normalized.maximum ?? normalized.exclusiveMaximum;
        this.exclusiveMinimum = normalized.exclusiveMinimum;
        this.exclusiveMaximum = normalized.exclusiveMaximum;

        if (normalized.multipleOf != null) {
            if (normalized.multipleOf.length > 0) {
                this.step = normalized.multipleOf[0];
            }
            if (normalized.multipleOf.length > 1) {
                this.extraMultiples = normalized.multipleOf;
            }
        }

        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
        }
    }

    // eslint-disable-next-line complexity
    valueChanged(newValue, oldValue) { // TODO value does not change for float input with integer
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue === ""));
        } else {
            this.dirty = this.initialData !== newValue;
        }
        let updatedValidStatus = false;
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            updatedValidStatus = true;
        }
        if (this.exclusiveMinimum != null || this.exclusiveMaximum != null) {
            this.boundsValid = (this.exclusiveMinimum == null || this.exclusiveMinimum < newValue) && (this.exclusiveMaximum == null || this.exclusiveMaximum > newValue);
            updatedValidStatus = true;
        }
        if (this.extraMultiples) {
            // TODO
        }
        if (updatedValidStatus) {
            this.updateValid();
        }
    }

    formInputChanged() {
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
        }
    }

    updateValid() {
        if (this.value == null) {
            if (this.isNullable) {
                this.valid = true;
                return;
            } else {
                this.valid = false;
                return;
            }
        }
        this.valid = this.formIsValid && this.boundsValid;
    }
}
