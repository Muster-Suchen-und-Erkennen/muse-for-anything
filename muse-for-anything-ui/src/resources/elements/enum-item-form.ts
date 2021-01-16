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
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: string | number | boolean | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    choices: SchemaDescription[] = [];
    @observable() selectedChoice: SchemaDescription;
    activeSchema: SchemaDescription;

    preferNumber: boolean = false;

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

        window.setTimeout(() => {
            this.updateSelectedSchema();
        }, 0);
    }

    valueChanged(newValue, oldValue) {
        this.updateSelectedSchema();
    }

    // eslint-disable-next-line complexity
    updateSelectedSchema() {
        const currentValue = this.value ?? this.initialData;
        let valueType: string;
        if (currentValue == null && this.activeSchema == null) {
            valueType = "Null";
        } else if (currentValue == null) {
            return;
        } else if (currentValue === Boolean(currentValue)) {
            valueType = "Boolean";
        } else if (currentValue === Number(currentValue)) {
            if (Number.isInteger(currentValue) && !this.preferNumber) {
                valueType = "Integer";
            } else {
                valueType = "Number";
            }
        } else {
            valueType = "String";
        }
        const idSuffix = `#/definitions/type${valueType}`;
        if (this.activeSchema?.schemaId?.endsWith(idSuffix)) {
            return; // schema already selected
        }
        const selectedChoice = this.choices.find(choice => choice.schemaId.endsWith(idSuffix));
        this.activeSchema = selectedChoice;
        if (this.selectedChoice == null) {
            this.selectedChoice = selectedChoice;
        }
        if (this.value == null) {
            this.valid = !this.required;
        } else {
            this.valid = true;
        }
    }

    selectedChoiceChanged(newValue: SchemaDescription) {
        if (this.activeSchema === newValue) {
            return;
        }
        if (newValue == null) {
            return;
        }
        const normalized = newValue.schema.normalized;
        this.activeSchema = null;
        if (normalized.const !== undefined) {
            this.value = normalized.const;
            return;
        }
        if (normalized.mainType === "boolean") {
            this.value = Boolean(this.value);
        }
        if (normalized.mainType === "integer" || normalized.mainType === "number") {
            this.preferNumber = normalized.mainType === "number";
            const numberValue = Number(this.value);
            if (this.value === numberValue) {
                // no value change, trigger manually
                this.updateSelectedSchema();
                return;
            }
            if (Number.isFinite(numberValue) && !Number.isNaN(numberValue)) {
                this.value = numberValue;
            } else {
                this.value = 0;
            }
        }
        if (normalized.mainType === "string") {
            this.value = this.value.toString();
        }
    }

}
