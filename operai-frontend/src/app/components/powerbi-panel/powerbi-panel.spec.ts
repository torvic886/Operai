import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PowerbiPanel } from './powerbi-panel';

describe('PowerbiPanel', () => {
  let component: PowerbiPanel;
  let fixture: ComponentFixture<PowerbiPanel>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PowerbiPanel]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PowerbiPanel);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
