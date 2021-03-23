import { bindable, observable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class TextForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: string;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: string;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: string;

    slug = nanoid(8);

    formIsValid: boolean = false;
    extraIsValid: boolean = true;

    isSingelLine: boolean = false;
    isNullable: boolean = true;

    format: string;

    minLength: number = null;
    maxLength: number = null;
    pattern: string = null;

    extraPatterns: RegExp[] = [];

    @child(".input-valid-check") formInput: Element;

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined && !this.dirty) {
            if (this.isNullable) {
                this.value = newValue;
            } else {
                this.value = newValue ?? "";
            }
            this.dirty = false;
        }
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;

            this.updateValid();
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.type.has("null");
        if (!this.isNullable && this.value == null) {
            this.value = "";
        }
        this.minLength = normalized.minLength;
        this.maxLength = normalized.maxLength;
        if (normalized.pattern != null && normalized.pattern.length === 1) {
            this.pattern = normalized.pattern[0].source;
            this.extraIsValid = true;
        } else {
            this.pattern = null;
            this.extraPatterns = normalized.pattern ?? [];
            this.extraIsValid = normalized.pattern == null;
        }
        if (normalized.format != null) {
            this.format = normalized.format;
        }
        if (normalized.contentMediaType != null) {
            // TODO
        }
        if ((normalized.maxLength != null && normalized.maxLength <= 500) || normalized.singleLine) {
            this.isSingelLine = true;
        } else {
            this.isSingelLine = false;
        }
        this.updateValid();
    }

    valueInChanged(newValue, oldValue) {
        // value change from outside
        if (this.isNullable) {
            this.value = newValue;
        } else {
            this.value = newValue ?? "";
        }
    }

    valueChanged(newValue, oldValue) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue === ""));
        } else {
            this.dirty = this.initialData !== newValue;
        }
        let updatedValidStatus = false;
        if (this.formInput != null) {
            updatedValidStatus = true;
        }
        if (this.extraPatterns) {
            this.extraIsValid = this.extraPatterns.every(pattern => pattern.test(newValue));
            updatedValidStatus = true;
        }
        this.valueOut = newValue;
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
            this.valid = this.isNullable;
            return;
        }
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
        } else {
            // console.log("no form input")
        }
        this.valid = this.formIsValid && this.extraIsValid;
    }
}
