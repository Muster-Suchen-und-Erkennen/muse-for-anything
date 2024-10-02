import { bindable, bindingMode, observable } from "aurelia-framework";
import { NormalizedApiSchema } from "rest/schema-objects";

interface SchemaDescription {
    title: string;
    description: string;
    schemaId: string;
    schema: NormalizedApiSchema;
}


export class EnumItemForm {
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

    choices: SchemaDescription[] = [];
    @observable() selectedChoice: SchemaDescription;
    activeSchema: SchemaDescription;

    @observable() childValid;

    // eslint-disable-next-line complexity
    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        this.valid = false;
        if (newValue == null) {
            return;
        }
        if (newValue.normalized.customType !== "enumItem") {
            return;
        }
        if (newValue.normalized.oneOf == null) {
            console.warn(this.key, newValue, this)
        }
        const rawChoices = [...(newValue.normalized.oneOf ?? [])];
        const choices = rawChoices.map(schema => {
            const normalized = schema.normalized;
            return {
                title: normalized.title ?? normalized.originRef,
                description: normalized.description ?? "",
                schemaId: normalized.$id,
                schema: schema,
            };
        });
        choices.sort((a, b) => {
            if (a.title > b.title) {
                return 1;
            }
            if (a.title < b.title) {
                return -1;
            }
            return 0;
        });
        this.choices = choices;

        if (this.valueIn !== undefined) {
            this.updateSelectedSchema(this.initialData);
        } else if (this.initialData !== undefined) {
            this.updateSelectedSchema(this.initialData);
        }
    }

    initialDataChanged(newValue) {
        if (newValue === undefined) {
            return;
        }
        if (this.selectedChoice == null) {
            this.updateSelectedSchema(this.initialData);
        }
    }

    valueInChanged(newValue, oldValue) {
        this.updateSelectedSchema(newValue);
    }

    valueChanged(newValue, oldValue) {
        this.valueOut = newValue;
    }

    valueOutChanged(newValue, oldValue) {
        if (this.initialData !== undefined) {
            this.dirty = newValue !== this.initialData;
        } else {
            this.dirty = newValue !== undefined;
        }

        this.childValidChanged();
    }

    childValidChanged() {
        if (this.valueOut == null) {
            this.valid = this.childValid && !this.required;
        } else {
            this.valid = this.childValid;
        }
    }

    // eslint-disable-next-line complexity
    updateSelectedSchema(value) {
        if (this.choices == null) {
            return;
        }
        let valueType: string;
        if (value == null && this.activeSchema == null) {
            valueType = "Null";
        } else if (value == null) {
            return;
        } else if (value === Boolean(value)) {
            valueType = "Boolean";
        } else if (value === Number(value)) {
            valueType = "Number";
        } else {
            valueType = "String";
        }
        const idSuffix = `#/definitions/type${valueType}`;
        if (this.activeSchema?.schemaId?.endsWith(idSuffix)) {
            return; // schema already selected
        }
        this.value = value;
        const selectedChoice = this.choices.find(choice => choice.schemaId.endsWith(idSuffix));
        this.activeSchema = selectedChoice;
        if (this.selectedChoice == null) {
            this.selectedChoice = selectedChoice;
        }
    }

    // eslint-disable-next-line complexity
    selectedChoiceChanged(newValue: SchemaDescription) {
        if (this.activeSchema === newValue) {
            return;
        }
        if (newValue == null) {
            return;
        }
        const normalized = newValue.schema.normalized;
        this.activeSchema = newValue;
        if (normalized.const !== undefined) {
            this.value = normalized.const;
            return;
        }
        if (normalized.mainType === "boolean") {
            this.value = Boolean(this.value);
        }
        if (normalized.mainType === "number") {
            const numberValue = Number(this.value);
            if (this.value === numberValue) {
                // no value change, trigger manually
                this.updateSelectedSchema(this.value);
                return;
            }
            if (Number.isFinite(numberValue) && !Number.isNaN(numberValue)) {
                this.value = numberValue;
            } else {
                this.value = 0;
            }
        }
        if (normalized.mainType === "string") {
            this.value = this.value?.toString() ?? "null";
        }
    }

}
