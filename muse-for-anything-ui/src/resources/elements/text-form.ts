import { autoinject, bindable, bindingMode, child, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";


@autoinject()
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

    inputType: string = "text";

    isSingelLine: boolean = false;
    isNullable: boolean = true;

    format: string;

    minLength: number = null;
    maxLength: number = null;
    pattern: string = null;

    extraPatterns: RegExp[] = [];

    @child(".input-valid-check") formInput: Element;

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            if (this.isNullable) {
                this.value = newValue;
            } else {
                this.value = newValue ?? "";
            }
            // schedule update for later to give input element time to catch up
            this.queue.queueMicroTask(() => this.updateValid());
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
        } else {
            this.pattern = null;
            this.extraPatterns = normalized.pattern ?? [];
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
        // TODO extend this to more input types
        if (normalized.password) {
            this.inputType = "password";
        } else {
            this.inputType = "text";
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
        this.valueOut = newValue;
    }

    valueOutChanged(newValue) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || (!this.isNullable && newValue === ""));
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateValid();
    }

    formInputChanged() {
        if (this.formInput != null) {
            // update valid again after value settles
            this.queue.queueMicroTask(() => this.updateValid());
        }
    }

    updateValid() {
        if (this.value == null) {
            this.valid = this.isNullable;
            return;
        }

        const value = this.valueOut;

        const formIsValid = (this.formInput as HTMLInputElement)?.validity?.valid ?? false;

        let extraIsValid = true;
        if (this.extraPatterns) {
            extraIsValid = this.extraPatterns.every(pattern => pattern.test(value));
        }

        this.valid = formIsValid && extraIsValid;
    }
}
