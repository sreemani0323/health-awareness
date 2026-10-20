import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'ha-get-involved',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './get-involved.component.html',
  styleUrl: './get-involved.component.css',
})
export class GetInvolvedComponent {}
