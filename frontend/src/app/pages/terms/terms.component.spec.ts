import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TermsComponent } from './terms.component';
import { RouterTestingModule } from '@angular/router/testing';

describe('TermsComponent', () => {
  let component: TermsComponent;
  let fixture: ComponentFixture<TermsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TermsComponent, RouterTestingModule]
    });
    fixture = TestBed.createComponent(TermsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display current date', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.last-updated')).toBeTruthy();
  });

  it('should have terms content', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Términos y Condiciones');
  });
});