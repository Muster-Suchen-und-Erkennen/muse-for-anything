import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";

type JSON_TYPES = "object" | "array" | "string" | "number" | "integer" | "boolean" | "null";

const VALID_JSON_TYPES: Set<JSON_TYPES> = new Set<JSON_TYPES>(["object", "array", "string", "number", "integer", "boolean", "null"]);

@autoinject()
export class JsonTypeForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: JSON_TYPES[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: JSON_TYPES[];
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: JSON_TYPES[] | null;

    slug = nanoid(8);

    isNullable: boolean = true;

    // broken out values from value array
    mainType: JSON_TYPES | null = null;
    expectedMainType: JSON_TYPES | null = null;
    typeContainsNull: boolean = false;

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            if (newValue == null || (Array.isArray(newValue) && newValue.every(v => VALID_JSON_TYPES.has(v)))) {
                // only assign valid type arrays (or null)
                this.value = newValue;
            }
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.type.has(null);
        const mustContain = normalized.contains?.normalized?.const ?? null;
        if (mustContain != null && VALID_JSON_TYPES.has(mustContain as JSON_TYPES)) {
            this.expectedMainType = mustContain as JSON_TYPES;
        }
        if (!this.isNullable && this.value == null) {
            if (this.expectedMainType != null) {
                this.value = [this.expectedMainType];
            } else {
                this.value = [];
            }
        }
        this.updateValid();
    }

    valueInChanged(newValue) {
        if (newValue == null || Array.isArray(newValue)) {
            this.value = newValue;
        }
    }

    valueChanged(newValue, oldValue) {
        if (newValue == null) {
            this.mainType = null;
            this.typeContainsNull = false;
            this.valueOut = [];
        } else if (Array.isArray(newValue)) {
            this.mainType = newValue.find(t => t !== "null");
            this.typeContainsNull = newValue.some(t => t === "null");
            const valueOut: JSON_TYPES[] = [];
            if (this.mainType != null) {
                valueOut.push(this.mainType);
            }
            if (this.typeContainsNull) {
                valueOut.push("null");
            }
            this.valueOut = valueOut;
        }
    }

    valueOutChanged(newValue) {
        if (this.initialData === undefined) {
            this.dirty = newValue != null;
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateValid();
    }

    updateValid() {
        if (this.schema == null) {
            this.valid = false;
            return;
        }
        this.queue.queueMicroTask(() => { // this prevents updates getting lost
            if (this.value == null) {
                this.valid = this.isNullable;
                return;
            }
            if (!Array.isArray(this.value)) {
                this.valid = false;  // not an array
                return;
            }
            if ((new Set(this.value)).size !== this.value.length) {
                this.valid = false;  // not all elements are unique
                return;
            }
            if (this.expectedMainType != null && !this.value.some(t => t === this.expectedMainType)) {
                this.valid = false;  // does not contain required type
                return;
            }
            const validMembersList = this.schema.normalized.items?.normalized?.enum ?? null;
            // eslint-disable-next-line no-ternary
            const validMembers = (validMembersList != null) ? new Set(validMembersList) : VALID_JSON_TYPES;
            this.valid = this.value.every(v => validMembers.has(v));
        });
    }

    toggleNullable(event) {
        const valueWithoutNull: JSON_TYPES[] = this.value?.filter?.(t => t !== "null") ?? [];
        if (event.target.checked) {
            this.value = [...valueWithoutNull, "null"];
        } else {
            this.value = valueWithoutNull;
        }
    }

    resetMainType() {
        if (this.expectedMainType == null) {
            return;
        }
        const oldValue = this.value?.filter?.(t => t === "null") ?? [];
        const newValue = [this.expectedMainType, ...oldValue];
        this.value = newValue;
    }

}
