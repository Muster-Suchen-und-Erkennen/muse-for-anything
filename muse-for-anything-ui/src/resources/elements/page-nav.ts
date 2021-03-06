import { bindable, autoinject } from "aurelia-framework";
import { BaseApiService } from "rest/base-api";
import { ApiResponse, ApiObject, ApiLink } from "rest/api-objects";

interface ClientLink {
    clientUrl: string;
    link: ApiLink;
}

interface ClientPageLink extends ClientLink {
    nr: number
}

@autoinject
export class PageNav {
    @bindable apiResponse;
    @bindable skipNavigation = false;

    isFirstPage: boolean = true;
    isLastPage: boolean = true;
    isOnlyPage: boolean = true;

    currentPageNumber: number = 1;
    lastPageNumber: number = 1;

    firstPage: ClientLink;
    lastPage: ClientLink;
    nextPage: ClientLink;
    previousPage: ClientLink;

    firstPageGap: boolean = false;
    lastPageGap: boolean = false;

    pages: ClientPageLink[] = [];

    private api: BaseApiService;

    constructor(baseApi: BaseApiService) {
        this.api = baseApi;
    }

    apiResponseChanged(newValue: ApiResponse<ApiObject>, oldValue) {
        const selfLink = newValue.data.self;
        const isFirstPage = selfLink.rel.some(rel => rel === "first");
        const isLastPage = selfLink.rel.some(rel => rel === "last");
        const isOnlyPage = isFirstPage && isLastPage;
        let currentPageNumber = 1;
        const resourceType = selfLink.resourceType;

        const promises = [];

        let firstPage: ClientLink;
        let lastPage: ClientLink;
        let nextPage: ClientLink;
        let previousPage: ClientLink;
        const pages: ClientPageLink[] = [];

        selfLink.rel.forEach(rel => {
            const match = rel.match(/^page-(?<page>\d+)$/);
            if (match != null) {
                const pageNumber = parseInt(match.groups.page, 10);
                currentPageNumber = pageNumber;
                const clientLink: ClientPageLink = { clientUrl: "", nr: pageNumber, link: selfLink };
                pages.push(clientLink);
                promises.push(this.api.buildClientUrl(selfLink).then(url => {
                    clientLink.clientUrl = url;
                }));
            }
        });

        newValue.links.forEach(link => {
            if (link.resourceType !== resourceType) {
                return; // not the correct resource type
            }
            if (!link.rel.some(rel => rel === "page")) {
                return; // not a page link
            }
            promises.push(this.api.buildClientUrl(link).then(url => {
                if (link.rel.some(rel => rel === "first")) {
                    firstPage = { clientUrl: url, link: link };
                }
                if (link.rel.some(rel => rel === "last")) {
                    lastPage = { clientUrl: url, link: link };
                }
                if (link.rel.some(rel => rel === "next")) {
                    nextPage = { clientUrl: url, link: link };
                }
                if (link.rel.some(rel => rel === "prev")) {
                    previousPage = { clientUrl: url, link: link };
                }
                link.rel.forEach(rel => {
                    const match = rel.match(/^page-(?<page>\d+)$/);
                    if (match != null) {
                        const pageNumber = parseInt(match.groups.page, 10);
                        if (!pages.some(page => page.nr === pageNumber)) {
                            pages.push({ clientUrl: url, nr: pageNumber, link: link });
                        }
                    }
                });
            }));
        });

        Promise.all(promises).then(() => {
            pages.sort((a, b) => a.nr - b.nr);

            if (pages.length > 1) {
                this.firstPageGap = (pages[0].nr + 1) < pages[1].nr;
                this.lastPageGap = (pages[pages.length - 2].nr + 1) < pages[pages.length - 1].nr;
            } else {
                this.firstPageGap = false;
                this.lastPageGap = false;
            }

            this.currentPageNumber = currentPageNumber;
            this.lastPageNumber = pages[pages.length - 1].nr;

            this.isFirstPage = isFirstPage;
            this.isLastPage = isLastPage;
            this.isOnlyPage = isOnlyPage;
            this.firstPage = firstPage;
            this.lastPage = lastPage;
            this.nextPage = nextPage;
            this.previousPage = previousPage;
            this.pages = pages;
        });
    }
}
