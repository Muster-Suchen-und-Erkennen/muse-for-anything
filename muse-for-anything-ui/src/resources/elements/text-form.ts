import { bindable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class TextForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: string;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

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
        this.isNullable = normalized.type.has(null) || !this.required;
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
        if (this.formInput != null) {
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            this.updateValid();
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
            this.formIsValid = (this.formInput as HTMLInputElement).validity.valid;
            updatedValidStatus = true;
        }
        if (this.extraPatterns) {
            this.extraIsValid = this.extraPatterns.every(pattern => pattern.test(newValue));
            updatedValidStatus = true;
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
        this.valid = this.formIsValid && this.extraIsValid;
    }
}
