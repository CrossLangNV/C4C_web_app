import { Directive, ElementRef } from '@angular/core';

declare const annotator: any;

@Directive({
  selector: '[appAnnotator]'
})
export class AnnotatorDirective {

  private callerElement:ElementRef;
  private documentId: number;
  private annotationType: string;

  constructor(el: ElementRef) {
    this.callerElement = el;
    this.documentId = el.nativeElement.getAttribute("doc-id");
    this.annotationType = el.nativeElement.getAttribute("annotation-type");
  }

  ngOnInit() {
    var app = new annotator.App();
    app.include(annotator.ui.main, {
      element: this.callerElement.nativeElement
    });
    app.include(annotator.storage.http, {
      prefix: 'http://localhost:8000/glossary/api/annotations/' + this.annotationType + "/" + this.documentId
    });
    app.start().then(function () {
      app.annotations.load();
    });
  }

}

