export interface SchemaValueObserver {
    onValueChanged: (key: string | number, newValue, oldValue) => void;
    onValidityChanged?: (key: string | number, newValue, oldValue) => void;
}
