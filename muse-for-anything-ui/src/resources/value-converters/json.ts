export class JsonValueConverter {
    toView(value) {
        return JSON.stringify(value, null, "\t");
    }

    fromView(value) {
        return JSON.parse(value);
    }
}
