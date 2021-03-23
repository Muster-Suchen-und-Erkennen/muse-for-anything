import { bindable, observable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class NumberForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: number;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: number;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: string;

    slug = nanoid(8);

    formIsValid: boolean = false;
    boundsValid: boolean = true;
    stepValid: boolean = true;

    isNullable: boolean = true;

    isInteger: boolean = true;

    step: number;

    minimum: number;
    maximum: number;

    exclusiveMinimum: number;
    exclusiveMaximum: number;

    extraMultiples: number[];

    @child(".input-valid-check") formInput: Element;

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            if (this.isNullable) {
                this.value = newValue?.toString() ?? "";
            } else {
                this.value = newValue?.toString() ?? "0";
            }
        }
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.type.has(null);
        if (!this.isNullable && this.value == null) {
            this.value = "0";
        }

        if (normalized.mainType === "integer") {
            this.step = 1;
            this.isInteger = true;
        } else {
            this.step = null;
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

    valueInChanged(newValue: number) {
        if (this.isNullable) {
            this.value = newValue?.toString() ?? "";
        } else {
            this.value = newValue?.toString() ?? "0";
        }
    }

    // eslint-disable-next-line complexity
    valueChanged(newValue: string, oldValue) { // TODO value does not change for float input with integer
        let newValueOut: number = null;
        if (newValue === "" || newValue == null) {
            this.valueOut = newValueOut;
            return;
        }
        if (this.isInteger) {
            newValueOut = parseInt(newValue, 10);
        } else {
            newValueOut = parseFloat(newValue);
        }
        this.valueOut = newValueOut;
    }

    valueOutChanged(newValue: number) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue == null));
        } else {
            this.dirty = this.initialData !== newValue;
        }

        // update validity
        if (this.exclusiveMinimum != null || this.exclusiveMaximum != null) {
            this.boundsValid = (this.exclusiveMinimum == null || this.exclusiveMinimum < newValue) && (this.exclusiveMaximum == null || this.exclusiveMaximum > newValue);
        }
        if (this.extraMultiples) {
            // TODO
        }
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
        }
        this.updateValid();
    }

    formInputChanged() {
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
        }
    }

    updateValid() {
        if (this.valueOut == null) {
            this.valid = this.isNullable;
            return;
        }
        const isNaN = Number.isNaN(this.valueOut);
        const isFinite = Number.isFinite(this.valueOut);
        this.valid = this.formIsValid && this.boundsValid && !isNaN && isFinite;
    }
}
