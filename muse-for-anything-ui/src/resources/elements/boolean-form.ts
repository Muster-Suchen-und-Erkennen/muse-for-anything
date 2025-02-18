import { autoinject, bindable, bindingMode, child, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";


@autoinject()
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

    showInfo: boolean = false;

    slug = nanoid(8);

    description: string = "";

    isNullable: boolean = true;

    @child(".input-valid-check") formInput: Element;

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    toggleInfo() {
        this.showInfo = !this.showInfo;
        return false;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            this.queue.queueMicroTask(() => {
                this.value = newValue;
            });
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.description = normalized.description ?? "";
        this.isNullable = normalized.type.has(null);
        if (!this.isNullable && this.value == null) {
            this.queue.queueMicroTask(() => {
                this.value = false;
            });
        } else {
            this.queue.queueMicroTask(() => {
                this.updateValid();
            });
        }
    }

    cycle(event?: Event) {
        event?.preventDefault();
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
    }

    valueInChanged(newValue, oldValue) {
        if (newValue == null && oldValue == null) {
            return;  // ignore updates from null to undefined and reverse
        }
        this.queue.queueMicroTask(() => {
            this.value = newValue;
        });
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
        if (this.schema == null) {
            this.queue.queueMicroTask(() => { // this prevents updates getting lost
                this.valid = false;
            });
            return;
        }
        this.queue.queueMicroTask(() => { // this prevents updates getting lost
            this.valid = this.isNullable || this.valueOut != null;
        });
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
