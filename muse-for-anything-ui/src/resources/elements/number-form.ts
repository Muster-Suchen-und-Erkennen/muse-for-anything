import { bindable, observable, bindingMode, child, TaskQueue, autoinject } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


@autoinject()
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

    isNullable: boolean = true;

    isInteger: boolean = true;

    step: number;

    minimum: number;
    maximum: number;

    exclusiveMinimum: number;
    exclusiveMaximum: number;

    extraMultiples: number[];

    @child(".input-valid-check") formInput: Element;

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            if (this.isNullable) {
                this.value = newValue?.toString() ?? "";
            } else {
                this.value = newValue?.toString() ?? "0";
            }
            // schedule update for later to give input element time to catch up
            this.queue.queueMicroTask(() => this.updateValid());
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
            this.valueOut = null;
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
        this.updateValid();
    }

    formInputChanged() {
        if (this.formInput != null) {
            // update valid again after value settles
            this.queue.queueMicroTask(() => this.updateValid());
        }
    }

    // eslint-disable-next-line complexity
    updateValid() {
        if (this.formInput == null) {
            return; // delays actually setting the value
        }
        if (this.valueOut == null) {
            this.valid = this.isNullable;
            return;
        }
        const value = this.valueOut;
        const formIsValid = (this.formInput as HTMLInputElement)?.validity?.valid ?? false;

        let boundsValid = true;
        if (this.exclusiveMinimum != null) {
            boundsValid &&= this.exclusiveMinimum < value;
        } else if (this.minimum != null) {
            boundsValid &&= this.minimum <= value;
        }
        if (this.exclusiveMaximum != null) {
            boundsValid &&= this.exclusiveMaximum > value;
        } else if (this.maximum != null) {
            boundsValid &&= this.maximum >= value;
        }

        let stepValid = true;
        if (this.extraMultiples) {
            // TODO
            stepValid = this.extraMultiples.every(step => (value % step) === 0);
        }

        const isNaN = Number.isNaN(value);
        const isFinite = Number.isFinite(value);
        this.valid = formIsValid && boundsValid && stepValid && !isNaN && isFinite;
    }
}
