import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";


@autoinject()
export class EnumForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: string | number | boolean | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: string | number | boolean | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: string | number | boolean | null;

    slug = nanoid(8);

    isNullable: boolean = true;

    enumChoices: Array<string | number | boolean | null> = [];

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            const initialDataChoice = this.enumChoices?.find(choice => choice === this.initialData) ?? undefined;
            if (initialDataChoice !== undefined) {
                this.value = initialDataChoice;
            }
        }
    }

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.isNullable = normalized.enum.some(item => item === null) || normalized.type?.has("null");
        const enumChoices = new Set(normalized.enum);
        if (this.isNullable) {
            enumChoices.add(null);
        }
        const enumChoicesArray = Array.from(enumChoices.keys());
        enumChoicesArray.sort((a, b) => {
            // sort null first
            if (a === null) {
                return -1;
            }
            if (b === null) {
                return 1;
            }
            // then booleans
            if (a === Boolean(a)) {
                if (b === false) {
                    return 1;
                }
                return -1;
            }
            if (b === Boolean(b)) {
                // only two booleans possible (either first if matches or only b is boolean)
                return 1;
            }
            // then numbers
            if (a === Number(a)) {
                if (b === Number(b)) {
                    return a - b;
                }
                return -1;
            }
            if (b === Number(b)) {
                return 1; // a cannot be a number after first if
            }
            // last strings
            if (a > b) {
                return 1;
            }
            if (a < b) {
                return -1;
            }
            return 0;
        });

        this.enumChoices = enumChoicesArray;

        if (!this.isNullable && this.value == null && enumChoicesArray.length > 0) {
            const initialDataChoice = this.enumChoices?.find(choice => choice === this.initialData) ?? undefined;
            if (initialDataChoice !== undefined) {
                this.value = initialDataChoice;
            } else {
                this.value = enumChoicesArray[0];
            }
        }
    }

    valueInChanged(newValue) {
        if (this.enumChoices?.some(choice => choice === newValue)) {
            this.value = newValue;
        }
    }

    valueChanged(newValue, oldValue) {
        this.queue.queueMicroTask(() => { // this is needed to properly propagate updates!
            this.valueOut = newValue;
        });
    }

    valueOutChanged(newValue) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || !this.isNullable);
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.valid = this.enumChoices?.some(choice => choice === this.value) ?? false;
    }

}
