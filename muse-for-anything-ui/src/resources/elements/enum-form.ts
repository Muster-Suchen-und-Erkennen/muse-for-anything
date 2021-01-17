import { bindable, bindingMode, child } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";
import { nanoid } from "nanoid";


export class EnumForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: string | number | boolean | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    slug = nanoid(8);

    isNullable: boolean = true;

    enumChoices: Array<string | number | boolean | null> = [];

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined && !this.dirty) {
            if (this.isNullable) {
                this.value = newValue;
            } else {
                this.value = newValue ?? false;
            }
            this.updateValid();
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
            this.value = enumChoicesArray[0];
        }
        this.updateValid();
    }

    valueChanged(newValue, oldValue) {
        if (this.initialData === undefined) {
            this.dirty = !(newValue == null || !this.isNullable);
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateValid();
    }

    updateValid() {
        window.setTimeout(() => {
            this.dirty = this.initialData !== this.value;
            this.valid = this.enumChoices?.some(choice => choice === this.value) ?? false;
        }, 1);
    }

}
