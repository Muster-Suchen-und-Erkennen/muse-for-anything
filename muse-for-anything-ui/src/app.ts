import { autoinject } from "aurelia-framework";

import { BaseApiService } from "rest/base-api";

@autoinject
export class App {
    public message = "Hello World!";

    constructor(baseApi: BaseApiService) {
        // query api by rel
        baseApi.getByRel("authentication").then(result => console.log(result));
        // search api for rel
        baseApi.searchResolveRels(["login", "post"]).then(result => console.log(result));
    }
}
