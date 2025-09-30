import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard.component';
import { RouterTestingModule } from '@angular/router/testing';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [DashboardComponent, RouterTestingModule]
    });
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display current time', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.update-time')).toBeTruthy();
  });

  it('should have risk levels section', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.risk-levels')).toBeTruthy();
  });
});