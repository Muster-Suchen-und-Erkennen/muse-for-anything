import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { NormalizedApiSchema } from "rest/schema-objects";
import { deepEqual } from "util/comparisons";

interface SchemaDescription {
    title: string;
    description: string;
    schema: NormalizedApiSchema;
}

@autoinject()
export class TypeDefinitionForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable debug: boolean = false;
    @bindable context: any;
    @bindable valuePush: any;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) valueIn: any;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) valueOut: any;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    @observable() value: any;

    slug = nanoid(8);

    choices: SchemaDescription[] = [];
    @observable() chosenSchema: SchemaDescription;
    initialDataChoice: SchemaDescription | null = null;

    @observable() nextActiveSchema: SchemaDescription;
    nextActiveValue: any;
    activeSchema: SchemaDescription;

    valueCache: Map<string, any> = new Map();

    @observable() childValid: boolean;

    private queue: TaskQueue;

    constructor(queue: TaskQueue) {
        this.queue = queue;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue) {
            const choice = this.getChoiceFromObjectData(newValue);
            this.initialDataChoice = choice;
            if (choice != null) {
                this.activeSchema = choice;
                this.chosenSchema = choice;
            }
        } else {
            this.initialDataChoice = null;
        }
    }

    // eslint-disable-next-line complexity
    getChoiceFromObjectData(data: any): SchemaDescription | null {
        if (!(this.choices?.length > 0)) {
            return null; // no choices to choose from
        }
        if (data == null) {
            return null; // no data to update from
        }
        let schemaId: string;
        const initialType = data.type ?? [];
        if (data.$ref != null) {
            schemaId = "#/definitions/ref";
        }
        if (initialType.some(t => t === "object")) {
            schemaId = "#/definitions/object";
            const customObjectType = data.customType;
            if (customObjectType === "resourceReference") {
                schemaId = "#/definitions/resourceReference";
            }
            // add more custom types here
        }
        if (initialType.some(t => t === "array")) {
            schemaId = "#/definitions/array";
            if (data.arrayType === "tuple") {
                schemaId = "#/definitions/tuple";
            }
        } else if (initialType.some(t => t === "string")) {
            schemaId = "#/definitions/string";
        } else if (initialType.some(t => t === "number")) {
            schemaId = "#/definitions/number";
        } else if (initialType.some(t => t === "integer")) {
            schemaId = "#/definitions/integer";
        } else if (initialType.some(t => t === "boolean")) {
            schemaId = "#/definitions/boolean";
        } else if (data.enum != null) {
            schemaId = "#/definitions/enum";
        }

        const choice = this.choices.find(choice => {
            return choice.schema.normalized.$id.endsWith(schemaId);
        });

        return choice;
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        if (newValue == null) {
            return;
        }
        if (newValue.normalized.customType !== "typeDefinition") {
            return;
        }
        if (newValue.normalized.oneOf == null) {
            console.warn(this.key, this.slug, newValue, this)
        }
        const rawChoices = [...(newValue.normalized.oneOf ?? [])];
        const choices = rawChoices.map(schema => {
            const normalized = schema.normalized;
            return {
                title: normalized.title ?? normalized.originRef,
                description: normalized.description ?? "",
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

        let choice;
        if (this.valueIn) {
            choice = this.getChoiceFromObjectData(this.valueIn);
        } else if (this.initialData) {
            choice = this.getChoiceFromObjectData(this.initialData);
        }
        if (choice != null && this.chosenSchema == null) {
            this.activeSchema = choice;
            this.chosenSchema = choice;
        }

        this.updateValid();
    }

    valueInChanged(newValue) {
        if (newValue?.type === "object") {
            console.error("Wrong input value!", newValue)
            return;
        }
        if (deepEqual(newValue, this.valueOut)) {
            return; // nothing has changed
        }
        const choice = this.getChoiceFromObjectData(newValue);
        if (choice != null && this.chosenSchema == null) {
            this.activeSchema = choice;
            this.chosenSchema = choice;
        }
        this.value = { ...newValue };
    }

    valueChanged(newValue, oldValue) {
        if (newValue == null) {
            return; // cannot be null
        }
        const newValueOut = { ...newValue };
        const containsChanges = !deepEqual(this.valueOut, newValue);
        if (containsChanges) {
            this.queue.queueMicroTask(() => this.valueOut = newValueOut);
        }
    }

    valueOutChanged(newValue) {
        this.updateValid();
    }

    childValidChanged() {
        this.updateValid();
    }

    updateValid() {
        this.queue.queueMicroTask(() => {
            if (this.valueOut == null) {
                this.valid = false; // this object type is never nullable
            } else {
                this.valid = this.childValid ?? false;
            }
        });
    }

    chosenSchemaChanged(newSchemaValue: SchemaDescription, oldSchemaValue: SchemaDescription) {
        if (this.activeSchema === newSchemaValue) {
            return; // change is from code to ui
        }
        const oldValue = this.value ?? {};
        if (oldSchemaValue != null) {
            this.valueCache.set(oldSchemaValue.title, { ...(oldValue ?? {}) });
        }
        this.activeSchema = null; // always set active schema to null first to reset child form
        if (newSchemaValue == null) {
            this.nextActiveValue = undefined;
            this.nextActiveSchema = null;
            this.value = null;
            return;
        }
        const newValue: any = {};
        if (newSchemaValue.schema.normalized.default != null) {
            const defaultValue = newSchemaValue.schema.normalized.default;
            Object.assign(newValue, JSON.parse(JSON.stringify(defaultValue)));
        }
        if (this.valueCache.has(newSchemaValue.title)) {
            const cachedValue = this.valueCache.get(newSchemaValue.title);
            Object.keys(cachedValue).forEach(key => {
                if (cachedValue[key] != null) {
                    newValue[key] = cachedValue[key];
                }
            });
        }
        ["title", "description", "$comment", "deprecated"].forEach(attr => {
            if (oldValue[attr] != null) {
                newValue[attr] = oldValue[attr];
            }
        });

        // set next active schema to user choice
        this.nextActiveValue = newValue;
        this.nextActiveSchema = newSchemaValue;
    }

    nextActiveSchemaChanged(newSchema) {
        this.queue.queueMicroTask(() => {
            if (this.nextActiveValue !== undefined) {
                const containsChanges = !deepEqual(this.valueOut, this.nextActiveValue);
                if (containsChanges && this.nextActiveValue != null) {
                    this.valueOut = { ...this.nextActiveValue };
                }
                this.value = this.nextActiveValue;
            }
            this.activeSchema = newSchema;
        });
    }
}
